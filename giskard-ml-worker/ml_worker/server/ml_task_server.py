import logging
from io import BytesIO

import cloudpickle
import pandas as pd
from ai_inspector import ModelInspector
from ai_inspector.io_utils import decompress
from zstandard import ZstdDecompressor

from generated.ml_worker_pb2 import RunTestRequest, TestResultMessage, RunModelResponse, RunModelRequest, DataFrame, \
    DataRow
from generated.ml_worker_pb2_grpc import MLWorkerServicer
from ml_worker.core.files_utils import read_model_file, read_dataset_file
from ml_worker.core.ml import run_predict
from ml_worker.testing.functions import GiskardTestFunctions
from mltask_server_runner import settings

logger = logging.getLogger()


class MLTaskServer(MLWorkerServicer):
    models_store = {}
    counter = 0

    def __init__(self, start_counter=0) -> None:
        super().__init__()
        self.counter = start_counter

    def runTest(self, request: RunTestRequest, context) -> TestResultMessage:
        root = settings.storage_root
        model_path = root / request.model_path

        tests = GiskardTestFunctions()
        _globals = {
            'model': read_model_file(str(model_path.absolute())),
            'tests': tests
        }
        if request.train_dataset_path:
            _globals['train_df'] = read_dataset_file(str((root / request.train_dataset_path).absolute()))
        if request.test_dataset_path:
            _globals['test_df'] = read_dataset_file(str((root / request.test_dataset_path).absolute()))

        exec(request.code, _globals)

        return TestResultMessage(results=tests.tests_results)

    def runModel(self, request: RunModelRequest, context) -> RunModelResponse:
        import numpy as np

        dzst = ZstdDecompressor()
        model_inspector: ModelInspector = cloudpickle.load(dzst.stream_reader(request.serialized_model))
        data_df = pd.read_csv(BytesIO(decompress(request.serialized_data)))
        # df = pd.DataFrame([r.features for r in request.data.rows])
        prediction_results = run_predict(data_df, model_inspector=model_inspector)

        if model_inspector.prediction_task == "classification":
            results = prediction_results.all_predictions
            labels = {k: v for k, v in enumerate(model_inspector.classification_labels)}
            label_serie = data_df[request.target]
            if len(model_inspector.classification_labels) > 2 or model_inspector.classification_threshold is None:
                preds_serie = prediction_results.all_predictions.idxmax(axis="columns")
                sorted_predictions = np.sort(prediction_results.all_predictions.values)
                abs_diff = pd.Series(sorted_predictions[:, -1] - sorted_predictions[:, -2], name="absDiff")
            else:
                diff = prediction_results.all_predictions.iloc[:, 1] - model_inspector.classification_threshold
                preds_serie = (diff >= 0).astype(int).map(labels).rename("predictions")
                abs_diff = pd.Series(diff.abs(), name="absDiff")
            calculated = pd.concat([preds_serie, label_serie, abs_diff], axis=1)
        else:
            results = pd.Series(prediction_results.prediction)
            predsSerie = results
            target_serie = data_df[request.target]
            abs_diff = pd.Series((predsSerie - target_serie).abs(), name="absDiff")
            abs_diff_percent = pd.Series(abs_diff / target_serie, name="absDiffPercent")
            calculated = pd.concat([predsSerie, target_serie, abs_diff, abs_diff_percent], axis=1)

        return RunModelResponse(
            results_csv=results.to_csv(index=False),
            calculated_csv=calculated.to_csv(index=False)
        )


        # return RunModelResponse(all_predictions=self.pandas_df_to_proto_df(predictions.all_predictions),
        #                         prediction=predictions.prediction.astype(str))
        return RunModelResponse(all_predictions_csv=predictions.all_predictions.to_csv(index=False),
                                prediction_csv=pd.Series(predictions.prediction).to_csv(index=False, header=False))

    @staticmethod
    def pandas_df_to_proto_df(df):
        return DataFrame(
            rows=[DataRow(features=r.astype(str).to_dict()) for _, r in df.iterrows()])

    @staticmethod
    def pandas_series_to_proto_series(self, series):
        return
