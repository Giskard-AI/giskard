import logging

from ai_inspector import ModelInspector

from ml_worker.core.files_utils import read_model_file, read_dataset_file

from generated.ml_worker_pb2 import RunTestRequest, TestResultMessage, RunModelResponse, RunModelRequest
from generated.ml_worker_pb2_grpc import MLWorkerServicer
from ml_worker.core.ml import run_predict
from ml_worker.testing.functions import GiskardTestFunctions
from mltask_server_runner import settings
import cloudpickle
import pandas as pd
from io import BytesIO
import pandas as pd

from zstandard import ZstdDecompressor
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

        dzst = ZstdDecompressor()
        model_inspector: ModelInspector = cloudpickle.load(dzst.stream_reader(request.serialized_model))
        df = pd.DataFrame([r.features for r in request.data.rows])
        predictions = run_predict(df, model_inspector=model_inspector)
        cloudpickle.loads(dzst.decompress(request.serialized_model))
        return RunModelResponse(prediction=1.23)
