import logging
import os
import platform
import re
import sys
import time
from io import StringIO

import google
import grpc
import numpy as np
import pandas as pd
import pkg_resources
import psutil
import tqdm
from google.protobuf.wrappers_pb2 import Int32Value, DoubleValue

import giskard
from giskard.client.giskard_client import GiskardClient
from giskard.core.model import Model
from giskard.ml_worker.core.dataset import Dataset
from giskard.ml_worker.core.model_explanation import (
    explain,
    explain_text,
)
from giskard.ml_worker.core.suite import Suite
from giskard.ml_worker.core.test_result import TestResult, TestMessageLevel
from giskard.ml_worker.core.test_runner import run_test
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.exceptions.giskard_exception import GiskardException
from giskard.ml_worker.generated import ml_worker_pb2
from giskard.ml_worker.generated.ml_worker_pb2_grpc import MLWorkerServicer
from giskard.ml_worker.testing.registry.registry import tests_registry
from giskard.ml_worker.utils.logging import Timer
from giskard.path_utils import model_path, dataset_path

logger = logging.getLogger(__name__)


def file_already_exists(meta: ml_worker_pb2.FileUploadMetadata):
    if meta.file_type == ml_worker_pb2.FileType.MODEL:
        path = model_path(meta.project_key, meta.name)
    elif meta.file_type == ml_worker_pb2.FileType.DATASET:
        path = dataset_path(meta.project_key, meta.name)
    else:
        raise ValueError(f"Illegal file type: {meta.file_type}")
    return path.exists(), path


class MLWorkerServiceImpl(MLWorkerServicer):
    def __init__(self, client: GiskardClient, address=None, remote=None) -> None:
        super().__init__()
        self.address = address
        self.remote = remote
        self.client = client

    def echo_orig(self, request, context):
        logger.debug(f"echo: {request.msg}")
        return ml_worker_pb2.EchoMsg(msg=request.msg)

    def upload(self, request_iterator, context: grpc.ServicerContext):
        meta = None
        path = None
        progress = None
        for upload_msg in request_iterator:
            if upload_msg.HasField("metadata"):
                meta = upload_msg.metadata
                file_exists, path = file_already_exists(meta)
                if not file_exists:
                    progress = tqdm.tqdm(
                        desc=f"Receiving {upload_msg.metadata.name}",
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                    )
                    yield ml_worker_pb2.UploadStatus(code=ml_worker_pb2.StatusCode.CacheMiss)
                else:
                    logger.info(f"File already exists: {path}")
                    break
            elif upload_msg.HasField("chunk"):
                try:
                    path.parent.mkdir(exist_ok=True, parents=True)
                    with open(path, "ab") as f:
                        f.write(upload_msg.chunk.content)
                    progress.update(len(upload_msg.chunk.content))
                except Exception as e:
                    if progress is not None:
                        progress.close()
                    logger.exception(f"Failed to upload file {meta.name}", e)
                    yield ml_worker_pb2.UploadStatus(code=ml_worker_pb2.StatusCode.Failed)

        if progress is not None:
            progress.close()
        yield ml_worker_pb2.UploadStatus(code=ml_worker_pb2.StatusCode.Ok)

    def getInfo(self, request: ml_worker_pb2.MLWorkerInfoRequest, context):
        logger.info("Collecting ML Worker info")
        installed_packages = (
            {p.project_name: p.version for p in pkg_resources.working_set} if request.list_packages else None
        )
        current_process = psutil.Process(os.getpid())
        return ml_worker_pb2.MLWorkerInfo(
            platform=ml_worker_pb2.PlatformInfo(
                machine=platform.uname().machine,
                node=platform.uname().node,
                processor=platform.uname().processor,
                release=platform.uname().release,
                system=platform.uname().system,
                version=platform.uname().version,
            ),
            giskard_client_version=giskard.__version__,
            pid=os.getpid(),
            process_start_time=int(current_process.create_time()),
            interpreter=sys.executable,
            interpreter_version=platform.python_version(),
            installed_packages=installed_packages,
            internal_grpc_address=self.address,
            is_remote=self.remote,
        )

    def echo(self, request: ml_worker_pb2.EchoMsg, context: grpc.ServicerContext) -> ml_worker_pb2.EchoMsg:
        return request

    def runAdHocTest(
            self, request: ml_worker_pb2.RunAdHocTestRequest, context: grpc.ServicerContext
    ) -> ml_worker_pb2.TestResultMessage:

        test = tests_registry.get_test(request.testId)

        arguments = self.parse_test_arguments(request.arguments)

        logger.info(f"Executing {test.name}")
        test_result = run_test(test.fn, arguments)

        return ml_worker_pb2.TestResultMessage(
            results=[
                ml_worker_pb2.NamedSingleTestResult(name=test.id, result=map_result_to_single_test_result(test_result))
            ]
        )

    def runTestSuite(
            self, request: ml_worker_pb2.RunTestSuiteRequest, context: grpc.ServicerContext
    ) -> ml_worker_pb2.TestSuiteResultMessage:
        tests = list(map(tests_registry.get_test, request.testId))

        global_arguments = self.parse_test_arguments(request.globalArguments)

        logger.info(f"Executing test suite: {list(map(lambda t: t.name, tests))}")

        suite = Suite()
        for test in tests:
            fixed_arguments = self.parse_test_arguments(
                next(x for x in request.fixedArguments if x.testId == test.id).arguments
            )
            suite.add_test(test.fn, **fixed_arguments)

        is_pass, results = suite.run(**global_arguments)

        result_list = list(results.values())

        named_single_test_result = []
        for i in range(len(tests)):
            named_single_test_result.append(
                ml_worker_pb2.NamedSingleTestResult(
                    name=tests[i].id, result=map_result_to_single_test_result(result_list[i])
                )
            )

        return ml_worker_pb2.TestSuiteResultMessage(is_pass=is_pass, results=named_single_test_result)

    def parse_test_arguments(self, request_arguments):
        arguments = {}
        for arg in request_arguments:
            if arg.HasField("dataset"):
                value = Dataset.load(self.client, arg.dataset.project_key, arg.dataset.id)
            elif arg.HasField("model"):
                value = Model.download(self.client, arg.model.project_key, arg.model.id)
            elif arg.HasField("float"):
                value = float(arg.float)
            elif arg.HasField("int"):
                value = int(arg.int)
            elif arg.HasField("str"):
                value = str(arg.str)
            elif arg.HasField("bool"):
                value = bool(arg.bool)
            else:
                raise IllegalArgumentError("Unknown argument type")
            arguments[arg.name] = value
        return arguments

    def runTest(
            self, request: ml_worker_pb2.RunTestRequest, context: grpc.ServicerContext
    ) -> ml_worker_pb2.TestResultMessage:
        from giskard.ml_worker.testing.functions import GiskardTestFunctions

        model = Model.download(self.client, request.model.project_key, request.model.id)

        tests = GiskardTestFunctions()
        _globals = {"model": model, "tests": tests}
        if request.reference_ds.id:
            _globals["reference_ds"] = Dataset.load(
                self.client, request.reference_ds.project_key, request.reference_ds.id
            )
        if request.actual_ds.id:
            _globals["actual_ds"] = Dataset.load(self.client, request.actual_ds.project_key, request.actual_ds.id)
        try:
            timer = Timer()
            exec(request.code, _globals)
            timer.stop(f"Test {tests.tests_results[0].name}")
        except NameError as e:
            missing_name = re.findall(r"name '(\w+)' is not defined", str(e))[0]
            if missing_name == "reference_ds":
                raise IllegalArgumentError("Reference Dataset is not specified")
            if missing_name == "actual_ds":
                raise IllegalArgumentError("Actual Dataset is not specified")
            raise e

        return ml_worker_pb2.TestResultMessage(results=tests.tests_results)

    def explain(self, request: ml_worker_pb2.ExplainRequest, context) -> ml_worker_pb2.ExplainResponse:
        model = Model.download(self.client, request.model.project_key, request.model.id)
        dataset = Dataset.load(self.client, request.dataset.project_key, request.dataset.id)
        explanations = explain(model, dataset, request.columns)

        return ml_worker_pb2.ExplainResponse(
            explanations={
                k: ml_worker_pb2.ExplainResponse.Explanation(per_feature=v)
                for k, v in explanations["explanations"].items()
            }
        )

    def explainText(self, request: ml_worker_pb2.ExplainTextRequest, context) -> ml_worker_pb2.ExplainTextResponse:
        n_samples = 500 if request.n_samples <= 0 else request.n_samples
        model = Model.download(self.client, request.model.project_key, request.model.id)
        text_column = request.feature_name

        if request.feature_types[text_column] != "text":
            raise ValueError(f"Column {text_column} is not of type text")
        text_document = request.columns[text_column]
        input_df = pd.DataFrame({k: [v] for k, v in request.columns.items()})
        if model.feature_names:
            input_df = input_df[model.feature_names]
        (list_words, list_weights) = explain_text(model, input_df, text_column, text_document, n_samples)
        map_features_weight = dict(zip(model.meta.classification_labels, list_weights))
        return ml_worker_pb2.ExplainTextResponse(
            weights={
                k: ml_worker_pb2.ExplainTextResponse.WeightsPerFeature(
                    weights=[weight for weight in map_features_weight[k]]
                )
                for k in map_features_weight
            },
            words=list_words,
        )

    def runModelForDataFrame(self, request: ml_worker_pb2.RunModelForDataFrameRequest, context):
        model = Model.download(self.client, request.model.project_key, request.model.id)
        ds = Dataset(
            pd.DataFrame([r.columns for r in request.dataframe.rows]),
            target=request.target,
            feature_types=request.feature_types,
        )
        predictions = model.predict(ds)
        if model.is_classification:
            return ml_worker_pb2.RunModelForDataFrameResponse(
                all_predictions=self.pandas_df_to_proto_df(predictions.all_predictions),
                prediction=predictions.prediction.astype(str),
            )
        else:
            return ml_worker_pb2.RunModelForDataFrameResponse(
                prediction=predictions.prediction.astype(str), raw_prediction=predictions.prediction
            )

    def runModel(self, request: ml_worker_pb2.RunModelRequest, context) -> ml_worker_pb2.RunModelResponse:
        try:
            model = Model.download(self.client, request.model.project_key, request.model.id)
            dataset = Dataset.load(self.client, request.dataset.project_key, request.dataset.id)
        except ValueError as e:
            if "unsupported pickle protocol" in str(e):
                raise ValueError(
                    "Unable to unpickle object, "
                    "Make sure that Python version of client code is the same as the Python version in ML Worker."
                    "To change Python version, please refer to https://docs.giskard.ai/start/guides/configuration"
                    f"\nOriginal Error: {e}"
                ) from e
            raise e
        except ModuleNotFoundError as e:
            raise GiskardException(
                f"Failed to import '{e.name}'. "
                f"Make sure it's installed in the ML Worker environment."
                "To install it, refer to https://docs.giskard.ai/start/guides/configuration"
            ) from e
        prediction_results = model.predict(dataset)

        if model.is_classification:
            results = prediction_results.all_predictions
            labels = {k: v for k, v in enumerate(model.meta.classification_labels)}
            label_serie = dataset.df[dataset.target] if dataset.target else None
            if len(model.meta.classification_labels) > 2 or model.meta.classification_threshold is None:
                preds_serie = prediction_results.all_predictions.idxmax(axis="columns")
                sorted_predictions = np.sort(prediction_results.all_predictions.values)
                abs_diff = pd.Series(sorted_predictions[:, -1] - sorted_predictions[:, -2], name="absDiff")
            else:
                diff = prediction_results.all_predictions.iloc[:, 1] - model.meta.classification_threshold
                preds_serie = (diff >= 0).astype(int).map(labels).rename("predictions")
                abs_diff = pd.Series(diff.abs(), name="absDiff")
            calculated = pd.concat([preds_serie, label_serie, abs_diff], axis=1)
        else:
            results = pd.Series(prediction_results.prediction)
            preds_serie = results
            if dataset.target and dataset.target in dataset.df.columns:
                target_serie = dataset.df[dataset.target]
                diff = preds_serie - target_serie
                diff_percent = pd.Series(diff / target_serie, name="diffPercent")
                abs_diff = pd.Series(diff.abs(), name="absDiff")
                abs_diff_percent = pd.Series(abs_diff / target_serie, name="absDiffPercent")
                calculated = pd.concat([preds_serie, target_serie, abs_diff, abs_diff_percent, diff_percent], axis=1)
            else:
                calculated = pd.concat([preds_serie], axis=1)

        return ml_worker_pb2.RunModelResponse(
            results_csv=results.to_csv(index=False), calculated_csv=calculated.to_csv(index=False)
        )

    def filterDataset(self, request_iterator, context: grpc.ServicerContext):
        filterfunc = {}
        meta = None

        times = []  # This is an array of chunk execution times for performance stats
        column_types = []

        for filter_msg in request_iterator:
            if filter_msg.HasField("meta"):
                meta = filter_msg.meta
                try:
                    exec(meta.function, None, filterfunc)
                except Exception as e:
                    yield ml_worker_pb2.FilterDatasetResponse(
                        code=ml_worker_pb2.StatusCode.Failed, error_message=str(e)
                    )
                column_types = meta.column_types
                logger.info(f"Filtering dataset with {meta}")
                yield ml_worker_pb2.FilterDatasetResponse(code=ml_worker_pb2.StatusCode.Ready)
            elif filter_msg.HasField("data"):
                logger.info("Got chunk " + str(filter_msg.idx))
                time_start = time.perf_counter()
                data_as_string = filter_msg.data.content.decode("utf-8")
                data_as_string = meta.headers + "\n" + data_as_string
                # CSV => Dataframe
                data = StringIO(data_as_string)  # Wrap using StringIO to avoid creating file
                df = pd.read_csv(data, keep_default_na=False, na_values=["_GSK_NA_"])
                df = df.astype(column_types)
                # Iterate over rows, applying filter_row func
                try:
                    rows_to_keep = df.apply(filterfunc["filter_row"], axis=1)[lambda x: x is True].index.array
                except Exception as e:
                    yield ml_worker_pb2.FilterDatasetResponse(
                        code=ml_worker_pb2.StatusCode.Failed, error_message=str(e)
                    )
                time_end = time.perf_counter()
                times.append(time_end - time_start)
                # Send NEXT code
                yield ml_worker_pb2.FilterDatasetResponse(
                    code=ml_worker_pb2.StatusCode.Next, idx=filter_msg.idx, rows=rows_to_keep
                )

        logger.info(f"Filter dataset finished. Avg chunk time: {sum(times) / len(times)}")
        yield ml_worker_pb2.FilterDatasetResponse(code=ml_worker_pb2.StatusCode.Ok)

    def getTestRegistry(
            self, request: google.protobuf.empty_pb2.Empty, context: grpc.ServicerContext
    ) -> ml_worker_pb2.TestRegistryResponse:
        return ml_worker_pb2.TestRegistryResponse(
            tests={
                test.id: ml_worker_pb2.TestFunction(
                    id=test.id,
                    name=test.name,
                    module=test.module,
                    doc=test.doc,
                    code=test.code,
                    module_doc=test.module_doc,
                    tags=test.tags,
                    arguments={
                        a.name: ml_worker_pb2.TestFunctionArgument(
                            name=a.name, type=a.type, optional=a.optional, default=str(a.default)
                        )
                        for a in test.args.values()
                    },
                )
                for test in tests_registry.get_all().values()
            }
        )

    @staticmethod
    def pandas_df_to_proto_df(df):
        return ml_worker_pb2.DataFrame(
            rows=[ml_worker_pb2.DataRow(columns=r.astype(str).to_dict()) for _, r in df.iterrows()]
        )

    @staticmethod
    def pandas_series_to_proto_series(self, series):
        return


def map_result_to_single_test_result(result) -> ml_worker_pb2.SingleTestResult:
    if isinstance(result, ml_worker_pb2.SingleTestResult):
        return result
    elif isinstance(result, TestResult):
        return ml_worker_pb2.SingleTestResult(
            passed=result.passed,
            messages=[
                ml_worker_pb2.TestMessage(
                    type=ml_worker_pb2.TestMessageType.ERROR
                    if message.type == TestMessageLevel.ERROR
                    else ml_worker_pb2.TestMessageType.INFO,
                    text=message.text,
                )
                for message in result.messages
            ],
            props=result.props,
            metric=result.metric,
            missing_count=Int32Value(value=result.missing_count),
            missing_percent=DoubleValue(value=result.missing_percent),
            unexpected_count=Int32Value(value=result.unexpected_count),
            unexpected_percent=DoubleValue(value=result.unexpected_percent),
            unexpected_percent_total=DoubleValue(value=result.unexpected_percent_total),
            unexpected_percent_nonmissing=DoubleValue(value=result.unexpected_percent_nonmissing),
            partial_unexpected_index_list=[
                ml_worker_pb2.Partial_unexpected_counts(value=puc.value, count=puc.count)
                for puc in result.partial_unexpected_index_list
            ],
            unexpected_index_list=result.unexpected_index_list,
            output_df=result.output_df,
            number_of_perturbed_rows=result.number_of_perturbed_rows,
            actual_slices_size=result.actual_slices_size,
            reference_slices_size=result.reference_slices_size,
        )
    elif isinstance(result, bool):
        return ml_worker_pb2.SingleTestResult(passed=result)
    else:
        raise ValueError("Result of test can only be 'GiskardTestResult' or 'bool'")
