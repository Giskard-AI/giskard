import logging

import ml_worker_pb2
from core.files_utils import read_dataset_file, read_model_file
from ml_worker_pb2_grpc import MLWorkerServicer
from mltask_server_runner import settings
from testing.functions import GiskardTestFunctions

logger = logging.getLogger()


class MLTaskServer(MLWorkerServicer):
    models_store = {}
    counter = 0

    def __init__(self, start_counter=0) -> None:
        super().__init__()
        self.counter = start_counter

    def runTest(self, request: ml_worker_pb2.RunTestRequest, context) -> ml_worker_pb2.TestResultMessage:
        model_path = settings.storage_root / request.model_path

        tests = GiskardTestFunctions()
        _globals = {
            'clf_predict': read_model_file(str(model_path.absolute())).prediction_function,
            'tests': tests
        }
        if request.train_dataset_path:
            _globals['train_df'] = read_dataset_file(str((settings.storage_root / request.train_dataset_path).absolute()))
        if request.test_dataset_path:
            _globals['test_df'] = read_dataset_file(str((settings.storage_root / request.test_dataset_path).absolute()))

        exec(request.code, _globals)

        return ml_worker_pb2.TestResultMessage(results=tests.tests_results)
