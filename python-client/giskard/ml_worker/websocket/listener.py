from enum import Enum
from pathlib import Path
from typing import List

import logging

import json
import stomp


import platform
import pkg_resources
import psutil
import sys
import os
import giskard

from giskard.core.suite import Suite, ModelInput, DatasetInput, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker import websocket
from giskard.ml_worker.core.log_listener import LogListener
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.exceptions.giskard_exception import GiskardException
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.registry import tests_registry
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import (
    TransformationFunction,
)
from giskard.ml_worker.testing.test_result import TestResult, TestMessageLevel
from giskard.ml_worker.ml_worker import MLWorker
from giskard.ml_worker.utils.file_utils import get_file_name
from giskard.ml_worker.websocket import (
    EchoMsg,
    ExplainParam,
    GetInfoParam,
    RunModelParam,
    TestSuiteParam,
    ExplainTextParam,
    RunAdHocTestParam,
    DatesetProcessingParam,
    GenerateTestSuiteParam,
    RunModelForDataFrameParam,
)
from giskard.models.base import BaseModel
from giskard.models.model_explanation import (
    explain,
    explain_text,
)
from giskard.path_utils import projects_dir

import math
import posixpath
import shutil
import tempfile

import numpy as np
import pandas as pd
from mlflow.store.artifact.artifact_repo import verify_artifact_path

import threading


logger = logging.getLogger(__name__)


class MLWorkerAction(Enum):
    getInfo = 0
    runAdHocTest = 1
    datasetProcessing = 2
    runTestSuite = 3
    runModel = 4
    runModelForDataFrame = 5
    explain = 6
    explainText = 7
    echo = 8
    generateTestSuite = 9
    stopWorker = 10
    getCatalog = 11
    generateQueryBasedSlicingFunction = 12


def websocket_log_actor(ml_worker: MLWorker, req: dict, *args, **kwargs):
    param = req["param"] if "param" in req.keys() else {}
    action = req["action"] if "action" in req.keys() else ""
    logger.info(f"ML Worker {ml_worker.ml_worker_id} performing {action} params: {param}")


WEBSOCKET_ACTORS = dict((action.name, websocket_log_actor) for action in MLWorkerAction)

MAX_STOMP_ML_WORKER_REPLY_SIZE = 1500


def action_in_thread(callback, ml_worker, action, req):
    # Parse the response ID
    rep_id = req["id"] if "id" in req.keys() else None
    # Parse the param
    params = req["param"] if "param" in req.keys() else {}
    try:
        # TODO: Sort by usage frequency
        if action == MLWorkerAction.getInfo:
            params = GetInfoParam.parse_obj(params)
        elif action == MLWorkerAction.runAdHocTest:
            params = RunAdHocTestParam.parse_obj(params)
        elif action == MLWorkerAction.datasetProcessing:
            params = DatesetProcessingParam.parse_obj(params)
        elif action == MLWorkerAction.runTestSuite:
            params = TestSuiteParam.parse_obj(params)
        elif action == MLWorkerAction.runModel:
            params = RunModelParam.parse_obj(params)
        elif action == MLWorkerAction.runModelForDataFrame:
            params = RunModelForDataFrameParam.parse_obj(params)
        elif action == MLWorkerAction.explain:
            params = ExplainParam.parse_obj(params)
        elif action == MLWorkerAction.explainText:
            params = ExplainTextParam.parse_obj(params)
        elif action == MLWorkerAction.echo:
            params = EchoMsg.parse_obj(params)
        elif action == MLWorkerAction.generateTestSuite:
            params = GenerateTestSuiteParam.parse_obj(params)
        elif action == MLWorkerAction.stopWorker:
            pass
        elif action == MLWorkerAction.getCatalog:
            pass
        elif action == MLWorkerAction.generateQueryBasedSlicingFunction:
            pass
        # Call the function and get the response
        info: websocket.WorkerReply = callback(ml_worker=ml_worker, action=action.name, params=params)
        # TODO: Allow to reply multiple messages for async event

    except Exception as e:
        info: websocket.WorkerReply = websocket.ErrorReply(error_str=str(e), error_type=type(e).__name__)
        logger.warn(e)

    if rep_id:
        # Reply if there is an ID
        # TODO: multiple shot, async
        logger.debug(f"[WRAPPED_CALLBACK] replying {len(info.json())} {info.json()} for {action.name}")
        # Message fragmentation
        FRAG_LEN = max(ml_worker.ws_max_reply_payload_size, MAX_STOMP_ML_WORKER_REPLY_SIZE)
        payload = info.json() if info else "{}"
        frag_count = math.ceil(len(payload) / FRAG_LEN)
        for frag_i in range(frag_count):
            ml_worker.ws_conn.send(
                f"/app/ml-worker/{ml_worker.ml_worker_id}/rep",
                json.dumps(
                    {
                        "id": rep_id,
                        "action": action.name,
                        "payload": payload[frag_i * FRAG_LEN : min((frag_i + 1) * FRAG_LEN, len(payload))],
                        "f_index": frag_i,
                        "f_count": frag_count,
                    }
                ),
            )

    # Post-processing of stopWorker
    if action == MLWorkerAction.stopWorker and ml_worker.ws_stopping is True:
        ml_worker.ws_conn.disconnect()


def websocket_actor(action: MLWorkerAction):
    """
    Register a function as an actor to an action from WebSocket connection
    """

    def websocket_actor_callback(callback: callable):
        if action in MLWorkerAction:
            logger.debug(f'Registered "{callback.__name__}" for ML Worker "{action.name}"')

            def wrapped_callback(ml_worker: MLWorker, req: dict, *args, **kwargs):
                # Open a new thread to process and reply, avoid slowing down the WebSocket message loop
                threading.Thread(target=action_in_thread, args=(callback, ml_worker, action, req)).start()

            WEBSOCKET_ACTORS[action.name] = wrapped_callback
        return callback

    return websocket_actor_callback


class MLWorkerWebSocketListener(stomp.ConnectionListener):
    subscribe_failed: bool = False

    def __init__(self, worker):
        self.ml_worker = worker

    def on_connected(self, frame):
        logger.debug(f"Connected: {frame}")
        self.ml_worker.ws_conn.subscribe(
            f"/ml-worker/{self.ml_worker.ml_worker_id}/action", f"ws-worker-{self.ml_worker.ml_worker_id}"
        )
        self.ml_worker.ws_conn.subscribe(
            f"/ml-worker/{self.ml_worker.ml_worker_id}/config", f"ws-worker-{self.ml_worker.ml_worker_id}"
        )

    def on_error(self, frame):
        logger.debug("received an error")
        if "message" in frame.headers.keys() and "Cannot find available worker" in frame.headers["message"]:
            self.subscribe_failed = True

    def on_disconnected(self):
        logger.debug("disconnected")
        if not self.subscribe_failed:
            # Attemp to reconnect
            self.ml_worker.connect_websocket_client()
        else:
            self.ml_worker.stop()

    def on_message(self, frame):
        logger.debug(f"received a message {frame.cmd} {frame.headers} {frame.body}")
        req = json.loads(frame.body)
        if "action" in req.keys() and req["action"] in WEBSOCKET_ACTORS:
            # Dispatch the action
            WEBSOCKET_ACTORS[req["action"]](self.ml_worker, req)
        elif "config" in req.keys():
            # Change the configuration
            if req["config"] == "MAX_STOMP_ML_WORKER_REPLY_SIZE" and "value" in req.keys():
                mtu = MAX_STOMP_ML_WORKER_REPLY_SIZE
                try:
                    mtu = max(mtu, int(req["value"]))
                except ValueError:
                    mtu = MAX_STOMP_ML_WORKER_REPLY_SIZE
                self.ml_worker.ws_max_reply_payload_size = mtu
                logger.info(f"MAX_STOMP_ML_WORKER_REPLY_SIZE set to {mtu}")


def map_function_meta_ws(callable_type):
    return {
        test.uuid: websocket.FunctionMeta(
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
                websocket.TestFunctionArgument(
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


def map_dataset_process_function_meta_ws(callable_type):
    return {
        test.uuid: websocket.DatasetProcessFunctionMeta(
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
                websocket.TestFunctionArgument(
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


@websocket_actor(MLWorkerAction.getInfo)
def on_ml_worker_get_info(ml_worker: MLWorker, params: GetInfoParam, *args, **kwargs) -> dict:
    logger.info("Collecting ML Worker info from WebSocket")

    installed_packages = (
        {p.project_name: p.version for p in pkg_resources.working_set} if params.list_packages else None
    )
    current_process = psutil.Process(os.getpid())
    return websocket.GetInfo(
        platform=websocket.Platform(
            machine=platform.uname().machine,
            node=platform.uname().node,
            processor=platform.uname().processor,
            release=platform.uname().release,
            system=platform.uname().system,
            version=platform.uname().version,
        ),
        giskardClientVersion=giskard.__version__,
        pid=os.getpid(),
        processStartTime=int(current_process.create_time()),
        interpreter=sys.executable,
        interpreterVersion=platform.python_version(),
        installedPackages=installed_packages,
        internalGrpcAddress=ml_worker.ml_worker_id,
        isRemote=ml_worker.is_remote_worker(),
    )


@websocket_actor(MLWorkerAction.stopWorker)
def on_ml_worker_stop_worker(ml_worker: MLWorker, *args, **kwargs):
    # Stop the server properly after sending disconnect
    logger.info("Stopping ML Worker")
    ml_worker.ws_stopping = True
    return websocket.Empty()


@websocket_actor(MLWorkerAction.runModel)
def run_model(ml_worker: MLWorker, params: websocket.RunModelParam, *args, **kwargs) -> websocket.Empty:
    try:
        model = BaseModel.download(ml_worker.client, params.model.project_key, params.model.id)
        dataset = Dataset.download(
            ml_worker.client,
            params.dataset.project_key,
            params.dataset.id,
            sample=params.dataset.sample,
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
        predictions_csv = get_file_name("predictions", "csv", params.dataset.sample)
        results.to_csv(index=False, path_or_buf=dir / predictions_csv)
        if ml_worker.client:
            ml_worker.client.log_artifact(
                dir / predictions_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )
        else:
            log_artifact_local(
                dir / predictions_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )

        calculated_csv = get_file_name("calculated", "csv", params.dataset.sample)
        calculated.to_csv(index=False, path_or_buf=dir / calculated_csv)
        if ml_worker.client:
            ml_worker.client.log_artifact(
                dir / calculated_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )
        else:
            log_artifact_local(
                dir / calculated_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )
    return websocket.Empty()


@websocket_actor(MLWorkerAction.runModelForDataFrame)
def run_model_for_data_frame(
    ml_worker: MLWorker, params: websocket.RunModelForDataFrameParam, *args, **kwargs
) -> websocket.RunModelForDataFrame:
    model = BaseModel.download(ml_worker.client, params.model.project_key, params.model.id)
    df = pd.DataFrame.from_records([r.columns for r in params.dataframe.rows])
    ds = Dataset(
        model.prepare_dataframe(df, column_dtypes=params.column_dtypes),
        target=None,
        column_types=params.column_types,
    )
    predictions = model.predict(ds)
    if model.is_classification:
        return websocket.RunModelForDataFrame(
            all_predictions=websocket.DataFrame(
                rows=[
                    websocket.DataRow(columns={str(k): v for k, v in r.astype(str).to_dict().items()})
                    for _, r in predictions.all_predictions.iterrows()
                ]
            ),
            prediction=list(predictions.prediction.astype(str)),
        )
    else:
        return websocket.RunModelForDataFrame(
            prediction=list(predictions.prediction.astype(str)),
            raw_prediction=list(predictions.prediction),
        )


@websocket_actor(MLWorkerAction.explain)
def explain_ws(ml_worker: MLWorker, params: websocket.ExplainParam, *args, **kwargs) -> websocket.Explain:
    model = BaseModel.download(ml_worker.client, params.model.project_key, params.model.id)
    dataset = Dataset.download(ml_worker.client, params.dataset.project_key, params.dataset.id, params.dataset.sample)
    explanations = explain(model, dataset, params.columns)

    return websocket.Explain(
        explanations={str(k): websocket.Explanation(per_feature=v) for k, v in explanations["explanations"].items()}
    )


@websocket_actor(MLWorkerAction.explainText)
def explain_text_ws(ml_worker: MLWorker, params: websocket.ExplainTextParam, *args, **kwargs) -> websocket.ExplainText:
    n_samples = 500 if params.n_samples <= 0 else params.n_samples
    model = BaseModel.download(ml_worker.client, params.model.project_key, params.model.id)
    text_column = params.feature_name

    if params.column_types[text_column] != "text":
        raise ValueError(f"Column {text_column} is not of type text")
    text_document = params.columns[text_column]
    input_df = pd.DataFrame({k: [v] for k, v in params.columns.items()})
    if model.meta.feature_names:
        input_df = input_df[model.meta.feature_names]
    (list_words, list_weights) = explain_text(model, input_df, text_column, text_document, n_samples)
    map_features_weight = dict(zip(model.meta.classification_labels, list_weights))
    return websocket.ExplainText(
        weights={
            str(k): websocket.WeightsPerFeature(weights=[weight for weight in map_features_weight[k]])
            for k in map_features_weight
        },
        words=list_words,
    )


@websocket_actor(MLWorkerAction.getCatalog)
def get_catalog(*args, **kwargs) -> websocket.Catalog:
    return websocket.Catalog(
        tests=map_function_meta_ws("TEST"),
        slices=map_dataset_process_function_meta_ws("SLICE"),
        transformations=map_dataset_process_function_meta_ws("TRANSFORMATION"),
    )


def parse_function_arguments(ml_worker: MLWorker, request_arguments: List[websocket.FuncArgument]):
    arguments = dict()

    # Processing empty list
    if not request_arguments:
        return arguments

    for arg in request_arguments:
        if arg.is_none:
            continue
        if arg.dataset:
            arguments[arg.name] = Dataset.download(
                ml_worker.client,
                arg.dataset.project_key,
                arg.dataset.id,
                arg.dataset.sample,
            )
        elif arg.model:
            arguments[arg.name] = BaseModel.download(ml_worker.client, arg.model.project_key, arg.model.id)
        elif arg.slicingFunction:
            arguments[arg.name] = SlicingFunction.download(arg.slicingFunction.id, ml_worker.client, None)(
                **parse_function_arguments(ml_worker, arg.args)
            )
        elif arg.transformationFunction:
            arguments[arg.name] = TransformationFunction.download(
                arg.transformationFunction.id, ml_worker.client, None
            )(**parse_function_arguments(ml_worker, arg.args))
        elif arg.float_arg:
            arguments[arg.name] = float(arg.float_arg)
        elif arg.int_arg:
            arguments[arg.name] = int(arg.int_arg)
        elif arg.str_arg:
            arguments[arg.name] = str(arg.str_arg)
        elif arg.bool_arg:
            arguments[arg.name] = bool(arg.bool_arg)
        elif arg.kwargs:
            kwargs = dict()
            exec(arg.kwargs, {"kwargs": kwargs})
            arguments.update(kwargs)
        else:
            raise IllegalArgumentError("Unknown argument type")
    return arguments


@websocket_actor(MLWorkerAction.datasetProcessing)
def dataset_processing(ml_worker: MLWorker, params: websocket.DatesetProcessingParam, *args, **kwargs):
    dataset = Dataset.download(ml_worker.client, params.dataset.project_key, params.dataset.id, params.dataset.sample)

    for function in params.functions:
        arguments = parse_function_arguments(ml_worker, function.arguments)
        if function.slicingFunction:
            dataset.add_slicing_function(
                SlicingFunction.download(function.slicingFunction.id, ml_worker.client, None)(**arguments)
            )
        else:
            dataset.add_transformation_function(
                TransformationFunction.download(function.transformationFunction.id, ml_worker.client, None)(**arguments)
            )

    result = dataset.process()

    filtered_rows_idx = dataset.df.index.difference(result.df.index)
    modified_rows = result.df[dataset.df.iloc[result.df.index].ne(result.df)].dropna(how="all")

    return websocket.DatasetProcessing(
        datasetId=params.dataset.id,
        totalRows=len(dataset.df.index),
        filteredRows=list(filtered_rows_idx),
        modifications=[
            websocket.DatasetRowModificationResult(
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


def map_result_to_single_test_result_ws(result) -> websocket.SingleTestResult:
    if isinstance(result, TestResult):
        return websocket.SingleTestResult(
            passed=result.passed,
            is_error=result.is_error,
            messages=[
                websocket.TestMessage(
                    type=websocket.TestMessageType.ERROR
                    if message.type == TestMessageLevel.ERROR.value
                    else websocket.TestMessageType.INFO,
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
                websocket.PartialUnexpectedCounts(value=puc.value, count=puc.count)
                for puc in result.partial_unexpected_index_list
            ],
            unexpected_index_list=result.unexpected_index_list,
            output_df=result.output_df,
            number_of_perturbed_rows=result.number_of_perturbed_rows,
            actual_slices_size=result.actual_slices_size,
            reference_slices_size=result.reference_slices_size,
        )
    elif isinstance(result, bool):
        return websocket.SingleTestResult(passed=result)
    else:
        raise ValueError("Result of test can only be 'TestResult' or 'bool'")


@websocket_actor(MLWorkerAction.runAdHocTest)
def run_ad_hoc_test(ml_worker: MLWorker, params: websocket.RunAdHocTestParam, *args, **kwargs):
    test: GiskardTest = GiskardTest.download(params.testUuid, ml_worker.client, None)

    arguments = parse_function_arguments(ml_worker, params.arguments)

    logger.info(f"Executing {test.meta.display_name or f'{test.meta.module}.{test.meta.name}'}")
    test_result = test.get_builder()(**arguments).execute()

    return websocket.RunAdHocTest(
        results=[
            websocket.NamedSingleTestResult(
                testUuid=test.meta.uuid, result=map_result_to_single_test_result_ws(test_result)
            )
        ]
    )


@websocket_actor(MLWorkerAction.runTestSuite)
def run_test_suite(ml_worker: MLWorker, params: websocket.TestSuiteParam, *args, **kwargs):
    log_listener = LogListener()
    try:
        tests = [
            {
                "test": GiskardTest.download(t.testUuid, ml_worker.client, None),
                "arguments": parse_function_arguments(ml_worker, t.arguments),
                "id": t.id,
            }
            for t in params.tests
        ]

        global_arguments = parse_function_arguments(ml_worker, params.globalArguments)

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

        is_pass, results = suite.run(**global_arguments)

        identifier_single_test_results = []
        for identifier, result in results:
            identifier_single_test_results.append(
                websocket.IdentifierSingleTestResult(id=identifier, result=map_result_to_single_test_result_ws(result))
            )

        return websocket.TestSuite(
            is_error=False,
            is_pass=is_pass,
            results=identifier_single_test_results,
            logs=log_listener.close(),
        )

    except Exception as exc:
        logger.exception("An error occurred during the test suite execution: %s", exc)
        return websocket.TestSuite(is_error=True, is_pass=False, results=[], logs=log_listener.close())


def map_suite_input_ws(i: websocket.SuiteInput):
    if i.type == "Model" and i.model_meta is not None:
        return ModelInput(i.name, i.model_meta.model_type)
    elif i.type == "Dataset" and i.dataset_meta is not None:
        return DatasetInput(i.name, i.dataset_meta.target)
    else:
        return SuiteInput(i.name, i.type)


@websocket_actor(MLWorkerAction.generateTestSuite)
def generate_test_suite(
    ml_worker: MLWorker, params: websocket.GenerateTestSuiteParam, *args, **kwargs
) -> websocket.GenerateTestSuite:
    inputs = [map_suite_input_ws(i) for i in params.inputs]

    suite = Suite().generate_tests(inputs).to_dto(ml_worker.client, params.project_key)

    return websocket.GenerateTestSuite(
        tests=[
            websocket.GeneratedTestSuite(
                test_uuid=test.testUuid,
                inputs=[
                    websocket.GeneratedTestInput(name=i.name, value=i.value, is_alias=i.is_alias)
                    for i in test.functionInputs.values()
                ],
            )
            for test in suite.tests
        ]
    )


@websocket_actor(MLWorkerAction.echo)
def echo(params: websocket.EchoMsg, *args, **kwargs) -> websocket.EchoMsg:
    return params
