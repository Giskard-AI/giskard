import asyncio
import logging
import math
import os
import platform
import posixpath
import shutil
import sys
import tempfile
import time
from io import StringIO
from pathlib import Path
from typing import Dict, Any

import google
import grpc
import numpy as np
import pandas as pd
import pkg_resources
import psutil
import tqdm
from mlflow.store.artifact.artifact_repo import verify_artifact_path

import giskard
from giskard.client.giskard_client import GiskardClient
from giskard.core.suite import Suite, ModelInput, DatasetInput, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker.core.log_listener import LogListener
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.exceptions.giskard_exception import GiskardException
from giskard.ml_worker.generated import ml_worker_pb2
from giskard.ml_worker.generated.ml_worker_pb2 import ArtifactRef, FuncArgument
from giskard.ml_worker.generated.ml_worker_pb2_grpc import MLWorkerServicer
from giskard.ml_worker.ml_worker import MLWorker
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.registry import tests_registry
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import (
    TransformationFunction,
)
from giskard.ml_worker.testing.test_result import TestResult, TestMessageLevel
from giskard.ml_worker.utils.file_utils import get_file_name
from giskard.models.base import BaseModel
from giskard.models.model_explanation import (
    explain,
    explain_text,
)
from giskard.path_utils import model_path, dataset_path, projects_dir

logger = logging.getLogger(__name__)


def extract_debug_info(request_arguments):
    template_info = " | <xxx:xxx_id>"
    info = {"suffix": "", "project_key": ""}
    for arg in request_arguments:
        if arg.HasField("model"):
            filled_info = template_info.replace("xxx", arg.name)
            info["suffix"] += filled_info.replace(arg.name + "_id", arg.model.id)
            info["project_key"] = arg.model.project_key  # in case model is in the args and dataset is not
        elif arg.HasField("dataset"):
            filled_info = template_info.replace("xxx", arg.name)
            info["suffix"] += filled_info.replace(arg.name + "_id", arg.dataset.id)
            info["project_key"] = arg.dataset.project_key  # in case dataset is in the args and model is not
    return info


def file_already_exists(meta: ml_worker_pb2.FileUploadMetadata):
    if meta.file_type == ml_worker_pb2.FileType.MODEL:
        path = model_path(meta.project_key, meta.name)
    elif meta.file_type == ml_worker_pb2.FileType.DATASET:
        path = dataset_path(meta.project_key, meta.name)
    else:
        raise ValueError(f"Illegal file type: {meta.file_type}")
    return path.exists(), path


def map_function_meta(callable_type):
    return {
        test.uuid: ml_worker_pb2.FunctionMeta(
            uuid=test.uuid,
            name=test.name,
            displayName=test.display_name,
            module=test.module,
            doc=test.doc,
            code=test.code,
            moduleDoc=test.module_doc,
            tags=test.tags,
            type=test.type,
            args=[
                ml_worker_pb2.TestFunctionArgument(
                    name=a.name,
                    type=a.type,
                    optional=a.optional,
                    default=str(a.default),
                    argOrder=a.argOrder,
                )
                for a in test.args.values()
            ],
        )
        for test in tests_registry.get_all().values()
        if test.type == callable_type
    }


def log_artifact_local(local_file, artifact_path=None):
    # Log artifact locally from an internal worker
    verify_artifact_path(artifact_path)

    file_name = os.path.basename(local_file)

    paths = (projects_dir, artifact_path, file_name) if artifact_path else (projects_dir, file_name)
    artifact_file = posixpath.join("/", *paths)
    Path(artifact_file).parent.mkdir(parents=True, exist_ok=True)

    shutil.copy(local_file, artifact_file)


def map_dataset_process_function_meta(callable_type):
    return {
        test.uuid: ml_worker_pb2.DatasetProcessFunctionMeta(
            uuid=test.uuid,
            name=test.name,
            displayName=test.display_name,
            module=test.module,
            doc=test.doc,
            code=test.code,
            moduleDoc=test.module_doc,
            tags=test.tags,
            type=test.type,
            args=[
                ml_worker_pb2.TestFunctionArgument(
                    name=a.name,
                    type=a.type,
                    optional=a.optional,
                    default=str(a.default),
                    argOrder=a.argOrder,
                )
                for a in test.args.values()
            ],
            cellLevel=test.cell_level,
            columnType=test.column_type,
            processType=test.process_type.name,
        )
        for test in tests_registry.get_all().values()
        if test.type == callable_type
    }


class MLWorkerServiceImpl(MLWorkerServicer):
    def __init__(
        self,
        ml_worker: MLWorker,
        client: GiskardClient,
        address=None,
        remote=None,
        loop=asyncio.get_event_loop(),
    ) -> None:
        super().__init__()
        self.ml_worker = ml_worker
        self.address = address
        self.remote = remote
        self.client = client
        self.loop = loop

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
        test: GiskardTest = GiskardTest.download(request.testUuid, self.client, None)

        arguments = self.parse_function_arguments(request.arguments)

        arguments["debug"] = request.debug if request.debug else None
        debug_info = extract_debug_info(request.arguments) if request.debug else None

        test_result = self.do_run_adhoc_test(self.client, arguments, test, debug_info)

        return ml_worker_pb2.TestResultMessage(
            results=[
                ml_worker_pb2.NamedSingleTestResult(
                    testUuid=test.meta.uuid,
                    result=map_result_to_single_test_result(test_result),
                )
            ]
        )

    @staticmethod
    def do_run_adhoc_test(client, arguments, test, debug_info=None):

        logger.info(f"Executing {test.meta.display_name or f'{test.meta.module}.{test.meta.name}'}")
        test_result = test.get_builder()(**arguments).execute()
        if test_result.output_df is not None:  # i.e. if debug is True and test has failed

            if debug_info is None:
                raise ValueError(
                    "You have requested to debug the test, "
                    "but extract_debug_info did not return the information needed."
                )

            test_result.output_df.name += debug_info["suffix"]

            test_result.output_df_id = test_result.output_df.upload(
                client=client, project_key=debug_info["project_key"]
            )
            # for now, we won't return output_df from grpc, rather upload it
            test_result.output_df = None
        elif arguments["debug"]:
            raise ValueError(
                "This test does not return any examples to debug. "
                "Check the debugging method associated to this test at "
                "https://docs.giskard.ai/en/latest/reference/tests/index.html"
            )

        return test_result

    def datasetProcessing(
        self,
        request: ml_worker_pb2.DatasetProcessingRequest,
        context: grpc.ServicerContext,
    ) -> ml_worker_pb2.DatasetProcessingResultMessage:
        dataset = Dataset.download(
            self.client,
            request.dataset.project_key,
            request.dataset.id,
            request.dataset.sample,
        )

        for function in request.functions:
            arguments = self.parse_function_arguments(function.arguments)
            if function.HasField("slicingFunction"):
                dataset.add_slicing_function(
                    SlicingFunction.download(
                        function.slicingFunction.id,
                        self.client,
                        function.slicingFunction.project_key or None,
                    )(**arguments)
                )
            else:
                dataset.add_transformation_function(
                    TransformationFunction.download(
                        function.transformationFunction.id,
                        self.client,
                        function.transformationFunction.project_key or None,
                    )(**arguments)
                )

        result = dataset.process()

        filtered_rows_idx = dataset.df.index.difference(result.df.index)
        modified_rows = result.df[dataset.df.iloc[result.df.index].ne(result.df)].dropna(how="all")

        return ml_worker_pb2.DatasetProcessingResultMessage(
            datasetId=request.dataset.id,
            totalRows=len(dataset.df.index),
            filteredRows=filtered_rows_idx,
            modifications=[
                ml_worker_pb2.DatasetRowModificationResult(
                    rowId=row[0],
                    modifications={
                        key: str(value)
                        for key, value in row[1].items()
                        if not type(value) == float or not math.isnan(value)
                    },
                )
                for row in modified_rows.iterrows()
            ],
        )

    def runTestSuite(
        self, request: ml_worker_pb2.RunTestSuiteRequest, context: grpc.ServicerContext
    ) -> ml_worker_pb2.TestSuiteResultMessage:
        log_listener = LogListener()
        try:
            tests = [
                {
                    "test": GiskardTest.download(t.testUuid, self.client, None),
                    "arguments": self.parse_function_arguments(t.arguments),
                    "id": t.id,
                }
                for t in request.tests
            ]

            global_arguments = self.parse_function_arguments(request.globalArguments)

            test_names = list(
                map(
                    lambda t: t["test"].meta.display_name or f"{t['test'].meta.module + '.' + t['test'].meta.name}",
                    tests,
                )
            )
            logger.info(f"Executing test suite: {test_names}")

            suite = Suite()
            for t in tests:
                suite.add_test(t["test"].get_builder()(**t["arguments"]), t["id"])

            result = suite.run(**global_arguments)

            identifier_single_test_results = []
            for identifier, result, args in result.results:
                identifier_single_test_results.append(
                    ml_worker_pb2.IdentifierSingleTestResult(
                        id=identifier,
                        result=map_result_to_single_test_result(result),
                        arguments=function_argument_to_proto(args),
                    )
                )

            return ml_worker_pb2.TestSuiteResultMessage(
                is_error=False,
                is_pass=result.passed,
                results=identifier_single_test_results,
                logs=log_listener.close(),
            )

        except Exception as exc:
            logger.exception("An error occurred during the test suite execution: %s", exc)
            return ml_worker_pb2.TestSuiteResultMessage(
                is_error=True, is_pass=False, results=[], logs=log_listener.close()
            )

    def parse_function_arguments(self, request_arguments):
        arguments = dict()

        for arg in request_arguments:
            if arg.none:
                continue
            if arg.HasField("dataset"):
                arguments[arg.name] = Dataset.download(
                    self.client,
                    arg.dataset.project_key,
                    arg.dataset.id,
                    arg.dataset.sample,
                )
            elif arg.HasField("model"):
                arguments[arg.name] = BaseModel.download(self.client, arg.model.project_key, arg.model.id)
            elif arg.HasField("slicingFunction"):
                arguments[arg.name] = SlicingFunction.download(arg.slicingFunction.id, self.client, None)(
                    **self.parse_function_arguments(arg.args)
                )
            elif arg.HasField("transformationFunction"):
                arguments[arg.name] = TransformationFunction.download(arg.transformationFunction.id, self.client, None)(
                    **self.parse_function_arguments(arg.args)
                )
            elif arg.HasField("float"):
                arguments[arg.name] = float(arg.float)
            elif arg.HasField("int"):
                arguments[arg.name] = int(arg.int)
            elif arg.HasField("str"):
                arguments[arg.name] = str(arg.str)
            elif arg.HasField("bool"):
                arguments[arg.name] = bool(arg.bool)
            elif arg.HasField("kwargs"):
                kwargs = dict()
                exec(arg.kwargs, {"kwargs": kwargs})
                arguments.update(kwargs)
            else:
                raise IllegalArgumentError("Unknown argument type")
        return arguments

    def explain(self, request: ml_worker_pb2.ExplainRequest, context) -> ml_worker_pb2.ExplainResponse:
        model = BaseModel.download(self.client, request.model.project_key, request.model.id)
        dataset = Dataset.download(
            self.client,
            request.dataset.project_key,
            request.dataset.id,
            request.dataset.sample,
        )
        explanations = explain(model, dataset, request.columns)

        return ml_worker_pb2.ExplainResponse(
            explanations={
                str(k): ml_worker_pb2.ExplainResponse.Explanation(per_feature=v)
                for k, v in explanations["explanations"].items()
            }
        )

    def explainText(self, request: ml_worker_pb2.ExplainTextRequest, context) -> ml_worker_pb2.ExplainTextResponse:
        model = BaseModel.download(self.client, request.model.project_key, request.model.id)
        text_column = request.feature_name

        if request.column_types[text_column] != "text":
            raise ValueError(f"Column {text_column} is not of type text")

        text_document = request.columns[text_column]
        input_df = pd.DataFrame({k: [v] for k, v in request.columns.items()})
        if model.meta.feature_names:
            input_df = input_df[model.meta.feature_names]
        (list_words, list_weights) = explain_text(model, input_df, text_column, text_document)
        map_features_weight = (
            dict(zip(model.meta.classification_labels, list_weights))
            if model.is_classification
            else {"WEIGHTS": list_weights}
        )
        return ml_worker_pb2.ExplainTextResponse(
            weights={
                str(k): ml_worker_pb2.ExplainTextResponse.WeightsPerFeature(
                    weights=[weight for weight in map_features_weight[k]]
                )
                for k in map_features_weight
            },
            words=list_words,
        )

    def runModelForDataFrame(self, request: ml_worker_pb2.RunModelForDataFrameRequest, context):
        model = BaseModel.download(self.client, request.model.project_key, request.model.id)
        df = pd.DataFrame.from_records([r.columns for r in request.dataframe.rows])
        ds = Dataset(
            model.prepare_dataframe(df, column_dtypes=request.column_dtypes),
            target=None,
            column_types=request.column_types,
        )
        predictions = model.predict(ds)
        if model.is_classification:
            return ml_worker_pb2.RunModelForDataFrameResponse(
                all_predictions=self.pandas_df_to_proto_df(predictions.all_predictions),
                prediction=predictions.prediction.astype(str),
            )
        else:
            return ml_worker_pb2.RunModelForDataFrameResponse(
                prediction=predictions.prediction.astype(str),
                raw_prediction=predictions.prediction,
            )

    def runModel(self, request: ml_worker_pb2.RunModelRequest, context) -> ml_worker_pb2.RunModelResponse:
        try:
            model = BaseModel.download(self.client, request.model.project_key, request.model.id)
            dataset = Dataset.download(
                self.client,
                request.dataset.project_key,
                request.dataset.id,
                sample=request.dataset.sample,
            )
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
                "To have more information on ML Worker, please see: https://docs.giskard.ai/start/guides/installation/ml-worker"
            ) from e
        prediction_results = model.predict(dataset)

        if model.is_classification:
            results = prediction_results.all_predictions
            labels = {k: v for k, v in enumerate(model.meta.classification_labels)}
            label_serie = dataset.df[dataset.target] if dataset.target else None
            if len(model.meta.classification_labels) > 2 or model.meta.classification_threshold is None:
                preds_serie = prediction_results.all_predictions.idxmax(axis="columns")
                sorted_predictions = np.sort(prediction_results.all_predictions.values)
                abs_diff = pd.Series(
                    sorted_predictions[:, -1] - sorted_predictions[:, -2],
                    name="absDiff",
                )
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
                diff_percent = pd.Series(
                    diff / target_serie,
                    name="diffPercent",
                    dtype=np.float64,
                ).replace([np.inf, -np.inf], np.nan)
                abs_diff = pd.Series(
                    diff.abs(),
                    name="absDiff",
                    dtype=np.float64,
                )
                abs_diff_percent = pd.Series(
                    abs_diff / target_serie,
                    name="absDiffPercent",
                    dtype=np.float64,
                ).replace([np.inf, -np.inf], np.nan)
                calculated = pd.concat(
                    [
                        preds_serie,
                        target_serie,
                        abs_diff,
                        abs_diff_percent,
                        diff_percent,
                    ],
                    axis=1,
                )
            else:
                calculated = pd.concat([preds_serie], axis=1)

        with tempfile.TemporaryDirectory(prefix="giskard-") as f:
            dir = Path(f)
            predictions_csv = get_file_name("predictions", "csv", request.dataset.sample)
            results.to_csv(index=False, path_or_buf=dir / predictions_csv)
            if self.ml_worker.tunnel:
                self.ml_worker.tunnel.client.log_artifact(
                    dir / predictions_csv,
                    f"{request.project_key}/models/inspections/{request.inspectionId}",
                )
            else:
                log_artifact_local(
                    dir / predictions_csv,
                    f"{request.project_key}/models/inspections/{request.inspectionId}",
                )

            calculated_csv = get_file_name("calculated", "csv", request.dataset.sample)
            calculated.to_csv(index=False, path_or_buf=dir / calculated_csv)
            if self.ml_worker.tunnel:
                self.ml_worker.tunnel.client.log_artifact(
                    dir / calculated_csv,
                    f"{request.project_key}/models/inspections/{request.inspectionId}",
                )
            else:
                log_artifact_local(
                    dir / calculated_csv,
                    f"{request.project_key}/models/inspections/{request.inspectionId}",
                )
        return google.protobuf.empty_pb2.Empty()

    def filterDataset(self, request_iterator, context: grpc.ServicerContext):
        filterfunc = {}
        meta = None

        times = []  # This is an array of chunk execution times for performance stats
        column_dtypes = []

        for filter_msg in request_iterator:
            if filter_msg.HasField("meta"):
                meta = filter_msg.meta
                try:
                    exec(meta.function, None, filterfunc)
                except Exception as e:
                    yield ml_worker_pb2.FilterDatasetResponse(
                        code=ml_worker_pb2.StatusCode.Failed, error_message=str(e)
                    )
                column_dtypes = meta.column_dtypes
                logger.info(f"Filtering dataset with {meta}")

                def filter_wrapper(row):
                    try:
                        return bool(filterfunc["filter_row"](row))
                    except Exception as e:  # noqa # NOSONAR
                        raise ValueError("Failed to execute user defined filtering function") from e

                yield ml_worker_pb2.FilterDatasetResponse(code=ml_worker_pb2.StatusCode.Ready)
            elif filter_msg.HasField("data"):
                logger.info("Got chunk " + str(filter_msg.idx))
                time_start = time.perf_counter()
                data_as_string = filter_msg.data.content.decode("utf-8")
                data_as_string = meta.headers + "\n" + data_as_string
                # CSV => Dataframe
                data = StringIO(data_as_string)  # Wrap using StringIO to avoid creating file
                df = pd.read_csv(data, keep_default_na=False, na_values=["_GSK_NA_"])
                df = df.astype(column_dtypes)
                # Iterate over rows, applying filter_row func
                try:
                    rows_to_keep = df[df.apply(filter_wrapper, axis=1)].index.array
                except Exception as e:
                    yield ml_worker_pb2.FilterDatasetResponse(
                        code=ml_worker_pb2.StatusCode.Failed, error_message=str(e)
                    )
                time_end = time.perf_counter()
                times.append(time_end - time_start)
                # Send NEXT code
                yield ml_worker_pb2.FilterDatasetResponse(
                    code=ml_worker_pb2.StatusCode.Next,
                    idx=filter_msg.idx,
                    rows=rows_to_keep,
                )

        logger.info(f"Filter dataset finished. Avg chunk time: {sum(times) / len(times)}")
        yield ml_worker_pb2.FilterDatasetResponse(code=ml_worker_pb2.StatusCode.Ok)

    @staticmethod
    def map_suite_input(i: ml_worker_pb2.SuiteInput):
        if i.type == "Model" and i.model_meta is not None:
            return ModelInput(i.name, i.model_meta.model_type)
        elif i.type == "Dataset" and i.dataset_meta is not None:
            return DatasetInput(i.name, i.dataset_meta.target)
        else:
            return SuiteInput(i.name, i.type)

    def generateTestSuite(
        self,
        request: ml_worker_pb2.GenerateTestSuiteRequest,
        context: grpc.ServicerContext,
    ) -> ml_worker_pb2.GenerateTestSuiteResponse:
        inputs = [self.map_suite_input(i) for i in request.inputs]

        suite = Suite().generate_tests(inputs).to_dto(self.client, request.project_key)

        return ml_worker_pb2.GenerateTestSuiteResponse(
            tests=[
                ml_worker_pb2.GeneratedTest(
                    test_uuid=test.testUuid,
                    inputs=[
                        ml_worker_pb2.GeneratedTestInput(name=i.name, value=i.value, is_alias=i.is_alias)
                        for i in test.functionInputs.values()
                    ],
                )
                for test in suite.tests
            ]
        )

    def stopWorker(
        self, request: google.protobuf.empty_pb2.Empty, context: grpc.ServicerContext
    ) -> google.protobuf.empty_pb2.Empty:
        logger.info("Received request to stop the worker")
        self.loop.create_task(self.ml_worker.stop())
        return google.protobuf.empty_pb2.Empty()

    def getCatalog(
        self, request: google.protobuf.empty_pb2.Empty, context: grpc.ServicerContext
    ) -> ml_worker_pb2.CatalogResponse:
        return ml_worker_pb2.CatalogResponse(
            tests=map_function_meta("TEST"),
            slices=map_dataset_process_function_meta("SLICE"),
            transformations=map_dataset_process_function_meta("TRANSFORMATION"),
        )

    @staticmethod
    def pandas_df_to_proto_df(df):
        return ml_worker_pb2.DataFrame(
            rows=[
                ml_worker_pb2.DataRow(columns={str(k): v for k, v in r.astype(str).to_dict().items()})
                for _, r in df.iterrows()
            ]
        )

    @staticmethod
    def pandas_series_to_proto_series(self, series):
        return


def map_result_to_single_test_result(result) -> ml_worker_pb2.SingleTestResult:
    if isinstance(result, ml_worker_pb2.SingleTestResult):
        return result
    elif isinstance(result, TestResult):
        return ml_worker_pb2.SingleTestResult(
            passed=bool(result.passed),
            is_error=result.is_error,
            messages=[
                ml_worker_pb2.TestMessage(
                    type=ml_worker_pb2.TestMessageType.ERROR
                    if message.type == TestMessageLevel.ERROR
                    else ml_worker_pb2.TestMessageType.INFO,
                    text=message.text,
                )
                for message in result.messages
            ]
            if result.messages is not None
            else [],
            props=result.props,
            metric=result.metric,
            missing_count=result.missing_count,
            missing_percent=result.missing_percent,
            unexpected_count=result.unexpected_count,
            unexpected_percent=result.unexpected_percent,
            unexpected_percent_total=result.unexpected_percent_total,
            unexpected_percent_nonmissing=result.unexpected_percent_nonmissing,
            partial_unexpected_index_list=[
                ml_worker_pb2.Partial_unexpected_counts(value=puc.value, count=puc.count)
                for puc in result.partial_unexpected_index_list
            ],
            unexpected_index_list=result.unexpected_index_list,
            output_df=None,
            number_of_perturbed_rows=result.number_of_perturbed_rows,
            actual_slices_size=result.actual_slices_size,
            reference_slices_size=result.reference_slices_size,
            output_df_id=result.output_df_id,
        )
    elif isinstance(result, bool):
        return ml_worker_pb2.SingleTestResult(passed=result)
    else:
        raise ValueError("Result of test can only be 'TestResult' or 'bool'")


def function_argument_to_proto(value: Dict[str, Any]):
    args = list()

    for v in value:
        obj = value[v]
        if isinstance(obj, Dataset):
            funcargs = FuncArgument(name=v, dataset=ArtifactRef(project_key="test", id=str(obj.id)))
        elif isinstance(obj, BaseModel):
            funcargs = FuncArgument(name=v, model=ArtifactRef(project_key="test", id=str(obj.id)))
        elif isinstance(obj, SlicingFunction):
            funcargs = FuncArgument(
                name=v,
                slicingFunction=ArtifactRef(project_key="test", id=str(obj.meta.uuid)),
                args=function_argument_to_proto(obj.params),
            )
        #     arguments[arg.name] = SlicingFunction.load(arg.slicingFunction.id, self.client, None)(
        #         **self.parse_function_arguments(arg.args))
        elif isinstance(obj, TransformationFunction):
            funcargs = FuncArgument(
                name=v,
                transformationFunction=ArtifactRef(project_key="test", id=str(obj.meta.uuid)),
                args=function_argument_to_proto(obj.params),
            )
        #     arguments[arg.name] = TransformationFunction.load(arg.transformationFunction.id, self.client, None)(
        #         **self.parse_function_arguments(arg.args))
        elif isinstance(obj, float):
            funcargs = FuncArgument(name=v, float=obj)
        elif isinstance(obj, int):
            funcargs = FuncArgument(name=v, int=obj)
        elif isinstance(obj, str):
            funcargs = FuncArgument(name=v, str=obj)
        elif isinstance(obj, bool):
            funcargs = FuncArgument(name=v, bool=obj)
        elif isinstance(obj, dict):
            funcargs = FuncArgument(name=v, kwargs=str(obj))
        else:
            raise IllegalArgumentError("Unknown argument type")
        args.append(funcargs)

    return args
