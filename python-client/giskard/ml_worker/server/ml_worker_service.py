import logging
import os
import platform
import re
import sys

import grpc
import numpy as np
import pandas as pd
import pkg_resources
import psutil
import tqdm

import giskard
from giskard.ml_worker.core.giskard_dataset import GiskardDataset
from giskard.ml_worker.core.model_explanation import (
    explain,
    parse_text_explainer_response,
    explain_text,
)
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.exceptions.giskard_exception import GiskardException
from giskard.ml_worker.generated.ml_worker_pb2 import (
    DataFrame,
    DataRow,
    EchoMsg,
    ExplainRequest,
    ExplainResponse,
    ExplainTextRequest,
    ExplainTextResponse,
    MLWorkerInfo,
    MLWorkerInfoRequest,
    PlatformInfo,
    RunModelForDataFrameRequest,
    RunModelForDataFrameResponse,
    RunModelRequest,
    RunModelResponse,
    RunTestRequest,
    TestResultMessage,
    UploadStatus,
    UploadStatusCode, FileUploadMetadata, FileType, )
from giskard.ml_worker.generated.ml_worker_pb2_grpc import MLWorkerServicer
from giskard.ml_worker.utils.grpc_mapper import deserialize_dataset, deserialize_model
from giskard.ml_worker.utils.logging import Timer
from giskard.path_utils import model_path, dataset_path

logger = logging.getLogger(__name__)

echo_count = 1


def file_already_exists(meta: FileUploadMetadata):
    if meta.file_type == FileType.MODEL:
        path = model_path(meta.project_key, meta.name)
    elif meta.file_type == FileType.DATASET:
        path = dataset_path(meta.project_key, meta.name)
    else:
        raise ValueError(f"Illegal file type: {meta.file_type}")
    return path.exists(), path


class MLWorkerServiceImpl(MLWorkerServicer):
    def __init__(self, port=None, remote=None) -> None:
        super().__init__()
        self.port = port
        self.remote = remote

    def echo(self, request, context):
        globals()["echo_count"] += 1
        return EchoMsg(msg=f"Response {echo_count}: {request.msg}")

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
                    yield UploadStatus(code=UploadStatusCode.CacheMiss)
                else:
                    logger.info(f"File already exists: {path}")
                    break
            elif upload_msg.HasField("chunk"):
                try:
                    path.parent.mkdir(exist_ok=True, parents=True)
                    with open(path, 'ab') as f:
                        f.write(upload_msg.chunk.content)
                    progress.update(len(upload_msg.chunk.content))
                except Exception as e:
                    if progress is not None:
                        progress.close()
                    logger.exception(f"Failed to upload file {meta.name}", e)
                    yield UploadStatus(code=UploadStatusCode.Failed)

        if progress is not None:
            progress.close()
        yield UploadStatus(code=UploadStatusCode.Ok)

    def getInfo(self, request: MLWorkerInfoRequest, context):
        installed_packages = (
            {p.project_name: p.version for p in pkg_resources.working_set}
            if request.list_packages
            else None
        )
        current_process = psutil.Process(os.getpid())
        return MLWorkerInfo(
            platform=PlatformInfo(
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
            internal_grpc_port=self.port,
            is_remote=self.remote,
        )

    def runTest(self, request: RunTestRequest, context: grpc.ServicerContext) -> TestResultMessage:
        from giskard.ml_worker.testing.functions import GiskardTestFunctions

        model = deserialize_model(request.model)

        tests = GiskardTestFunctions()
        _globals = {"model": model, "tests": tests}
        if request.reference_ds.file_name:
            _globals["reference_ds"] = deserialize_dataset(request.reference_ds)
        if request.actual_ds.file_name:
            _globals["actual_ds"] = deserialize_dataset(request.actual_ds)
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

        return TestResultMessage(results=tests.tests_results)

    def explain(self, request: ExplainRequest, context) -> ExplainResponse:
        model = deserialize_model(request.model)
        dataset = deserialize_dataset(request.dataset)
        explanations = explain(model, dataset, request.columns)

        return ExplainResponse(
            explanations={
                k: ExplainResponse.Explanation(per_feature=v)
                for k, v in explanations["explanations"].items()
            }
        )

    def explainText(self, request: ExplainTextRequest, context) -> ExplainTextResponse:
        n_samples = 500 if request.n_samples <= 0 else request.n_samples
        model = deserialize_model(request.model)
        text_column = request.feature_name

        if request.feature_types[text_column] != "text":
            raise ValueError(f"Column {text_column} is not of type text")
        text_document = request.columns[text_column]
        input_df = pd.DataFrame({k: [v] for k, v in request.columns.items()})
        if model.feature_names:
            input_df = input_df[model.feature_names]

        html_response = explain_text(model, input_df, text_column, text_document, n_samples)._repr_html_()
        return ExplainTextResponse(explanations=parse_text_explainer_response(html_response))

    def runModelForDataFrame(self, request: RunModelForDataFrameRequest, context):
        model = deserialize_model(request.model)
        ds = GiskardDataset(
            pd.DataFrame([r.columns for r in request.dataframe.rows]),
            target=request.target,
            feature_types=request.feature_types,
            column_types=request.column_types,
        )
        predictions = model.run_predict(ds)
        if model.model_type == "classification":
            return RunModelForDataFrameResponse(
                all_predictions=self.pandas_df_to_proto_df(predictions.all_predictions),
                prediction=predictions.prediction.astype(str),
            )
        else:
            return RunModelForDataFrameResponse(
                prediction=predictions.prediction.astype(str), raw_prediction=predictions.prediction
            )

    def runModel(self, request: RunModelRequest, context) -> RunModelResponse:
        try:
            model = deserialize_model(request.model)
            dataset = deserialize_dataset(request.dataset)
        except ValueError as e:
            if "unsupported pickle protocol" in str(e):
                raise ValueError('Unable to unpickle object, '
                                 'Make sure that Python version of client code is the same as the Python version in ML Worker.'
                                 'To change Python version, please refer to https://docs.giskard.ai/start/guides/configuration'
                                 f'\nOriginal Error: {e}') from e
            raise e
        except ModuleNotFoundError as e:
            raise GiskardException(f"Failed to import '{e.name}'. "
                                   f"Make sure it's installed in the ML Worker environment."
                                   "To install it, refer to https://docs.giskard.ai/start/guides/configuration") from e
        prediction_results = model.run_predict(dataset)

        if model.model_type == "classification":
            results = prediction_results.all_predictions
            labels = {k: v for k, v in enumerate(model.classification_labels)}
            label_serie = dataset.df[dataset.target] if dataset.target else None
            if len(model.classification_labels) > 2 or model.classification_threshold is None:
                preds_serie = prediction_results.all_predictions.idxmax(axis="columns")
                sorted_predictions = np.sort(prediction_results.all_predictions.values)
                abs_diff = pd.Series(
                    sorted_predictions[:, -1] - sorted_predictions[:, -2], name="absDiff"
                )
            else:
                diff = (
                        prediction_results.all_predictions.iloc[:, 1] - model.classification_threshold
                )
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
                calculated = pd.concat(
                    [preds_serie, target_serie, abs_diff, abs_diff_percent, diff_percent], axis=1
                )
            else:
                calculated = pd.concat([preds_serie], axis=1)

        return RunModelResponse(
            results_csv=results.to_csv(index=False), calculated_csv=calculated.to_csv(index=False)
        )

    @staticmethod
    def pandas_df_to_proto_df(df):
        return DataFrame(rows=[DataRow(columns=r.astype(str).to_dict()) for _, r in df.iterrows()])

    @staticmethod
    def pandas_series_to_proto_series(self, series):
        return
