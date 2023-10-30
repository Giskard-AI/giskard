from typing import Any, Callable, Dict, Optional, Union

import asyncio
import logging
import os
import platform
import sys
import tempfile
import time
import traceback
from concurrent.futures import CancelledError, Future
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pkg_resources
import psutil

import giskard
from giskard.client.giskard_client import GiskardClient
from giskard.core.suite import Suite
from giskard.datasets.base import Dataset
from giskard.ml_worker import websocket
from giskard.ml_worker.core.log_listener import LogListener
from giskard.ml_worker.core.savable import RegistryArtifact
from giskard.ml_worker.exceptions.giskard_exception import GiskardException
from giskard.ml_worker.stomp.parsing import Frame
from giskard.ml_worker.testing.registry.giskard_test import GiskardTest
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
from giskard.ml_worker.utils.file_utils import get_file_name
from giskard.ml_worker.websocket import CallToActionKind, GetInfoParam, PushKind
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.ml_worker.websocket.utils import (
    do_run_adhoc_test,
    extract_debug_info,
    function_argument_to_ws,
    log_artifact_local,
    map_dataset_process_function_meta_ws,
    map_function_meta_ws,
    map_result_to_single_test_result_ws,
    map_suite_input_ws,
    parse_action_param,
    parse_function_arguments,
)
from giskard.models.base import BaseModel
from giskard.models.model_explanation import explain, explain_text
from giskard.push import Push
from giskard.settings import settings
from giskard.utils import call_in_pool
from giskard.utils.analytics_collector import analytics

logger = logging.getLogger(__name__)


MAX_STOMP_ML_WORKER_REPLY_SIZE = 1500


@dataclass
class MLWorkerInfo:
    id: str
    is_remote: bool


def websocket_log_actor(ml_worker: MLWorkerInfo, req: Dict, *args, **kwargs):
    param = req["param"] if "param" in req.keys() else {}
    action = req["action"] if "action" in req.keys() else ""
    logger.info(f"ML Worker {ml_worker.id} performing {action} params: {param}")


WEBSOCKET_ACTORS = dict((action.name, websocket_log_actor) for action in MLWorkerAction)


def wrapped_handle_result(
    action: MLWorkerAction, start: float, rep_id: Optional[str], worker_info: MLWorkerInfo, ignore_timeout: bool
):
    async def handle_result(future: Union[Future, Callable[..., websocket.WorkerReply]]):
        info = None  # Needs to be defined in case of cancellation

        try:
            info: websocket.WorkerReply = (
                await asyncio.wait_for(asyncio.wrap_future(future, loop=asyncio.get_running_loop()), timeout=None)
                if isinstance(future, Future)
                else future()
            )
        except (CancelledError, asyncio.exceptions.CancelledError) as e:
            if ignore_timeout:
                info: websocket.WorkerReply = websocket.Empty()
                logger.warning("Task for %s has timed out and been cancelled", action.name)
            else:
                info: websocket.WorkerReply = websocket.ErrorReply(
                    error_str=str(e), error_type=type(e).__name__, detail=traceback.format_exc()
                )
                logger.warning(e)
        except BaseException as e:
            info: websocket.WorkerReply = websocket.ErrorReply(
                error_str=str(e), error_type=type(e).__name__, detail=traceback.format_exc()
            )
            logger.exception(e)
        finally:
            analytics.track(
                "mlworker:websocket:action",
                {
                    "name": action.name,
                    "worker": worker_info.id,
                    "language": "PYTHON",
                    "type": "ERROR" if isinstance(info, websocket.ErrorReply) else "SUCCESS",
                    "action_time": time.process_time() - start,
                    "error": info.error_str if isinstance(info, websocket.ErrorReply) else "",
                    "error_type": info.error_type if isinstance(info, websocket.ErrorReply) else "",
                },
            )

        if rep_id:
            if isinstance(info, Frame):
                return info
            return info.json(by_alias=True) if info else "{}"

    return handle_result


def parse_and_execute(
    *,
    callback: Callable,
    action: MLWorkerAction,
    params,
    ml_worker: MLWorkerInfo,
    client_params: Optional[Dict[str, str]],
) -> websocket.WorkerReply:
    action_params = parse_action_param(action, params)
    return callback(
        ml_worker=ml_worker,
        client=GiskardClient(**client_params) if client_params is not None else None,
        action=action.name,
        params=action_params,
    )


async def dispatch_action(
    callback: Callable,
    action: MLWorkerAction,
    req: Dict[str, Any],
    client_params: Dict[str, Any],
    worker_info: MLWorkerInfo,
    execute_in_pool: bool,
    timeout: Optional[float] = None,
    ignore_timeout=False,
):
    # Parse the response ID
    rep_id = req["id"] if "id" in req.keys() else None
    # Parse the param
    params = req["param"] if "param" in req.keys() else {}

    # Track usage frequency to optimize action param parsing
    analytics.track(
        "mlworker:websocket:action:type",
        {
            "name": action.name,
            "worker": worker_info.id,
            "language": "PYTHON",
        },
    )
    start = time.process_time()

    result_handler = wrapped_handle_result(action, start, rep_id, worker_info, ignore_timeout=ignore_timeout)
    # If execution should be done in a pool
    if execute_in_pool and settings.use_pool:
        logger.debug("Submitting for action %s '%s' into the pool", action.name, callback.__name__)
        kwargs = {
            "callback": callback,
            "action": action,
            "params": params,
            "ml_worker": worker_info,
            "client_params": client_params,
        }

        future = call_in_pool(
            parse_and_execute,
            kwargs=kwargs,
            timeout=timeout,
        )
    else:

        def future():
            return parse_and_execute(
                callback=callback, action=action, params=params, ml_worker=worker_info, client_params=client_params
            )

    return await result_handler(future)


def websocket_actor(
    action: MLWorkerAction, execute_in_pool: bool = True, timeout: Optional[float] = None, ignore_timeout: bool = False
):
    """
    Register a function as an actor to an action from WebSocket connection
    """

    def websocket_actor_callback(callback: callable):
        if action not in MLWorkerAction:
            raise NotImplementedError(f"Missing implementation for {action}, not in MLWorkerAction")
        logger.debug(f'Registered "{callback.__name__}" for ML Worker "{action.name}"')

        async def wrapped_callback(req: Dict, client_params: Dict, worker_info, *args, **kwargs):
            return await dispatch_action(
                callback, action, req, client_params, worker_info, execute_in_pool, timeout, ignore_timeout
            )

        WEBSOCKET_ACTORS[action.name] = wrapped_callback

        return callback

    return websocket_actor_callback


@websocket_actor(MLWorkerAction.getInfo, execute_in_pool=False)
def on_ml_worker_get_info(ml_worker: MLWorkerInfo, params: GetInfoParam, *args, **kwargs) -> websocket.GetInfo:
    logger.info("Collecting ML Worker info from WebSocket")

    # TODO(Bazire): seems to be deprecated https://setuptools.pypa.io/en/latest/pkg_resources.html#workingset-objects
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
        mlWorkerId=ml_worker.id,
        isRemote=ml_worker.is_remote,
    )


@websocket_actor(MLWorkerAction.stopWorker, execute_in_pool=False)
def on_ml_worker_stop_worker(*args, **kwargs) -> websocket.Empty:
    # Stop the server properly after sending disconnect
    logger.info("Stopping ML Worker")
    return None


def run_classification_mode(model, dataset, prediction_results):
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
    return results, calculated


def run_other_model(dataset, prediction_results):
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
    return results, calculated


@websocket_actor(MLWorkerAction.runModel)
def run_model(client: GiskardClient, params: websocket.RunModelParam, *args, **kwargs) -> websocket.Empty:
    try:
        model = BaseModel.download(client, params.model.project_key, params.model.id)
        dataset = Dataset.download(
            client,
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
        results, calculated = run_classification_mode(model, dataset, prediction_results)
    else:
        results, calculated = run_other_model(dataset, prediction_results)

    with tempfile.TemporaryDirectory(prefix="giskard-") as f:
        tmp_dir = Path(f)
        predictions_csv = get_file_name("predictions", "csv", params.dataset.sample)
        results.to_csv(index=False, path_or_buf=tmp_dir / predictions_csv)
        if client:
            client.log_artifact(
                tmp_dir / predictions_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )
        else:
            log_artifact_local(
                tmp_dir / predictions_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )

        calculated_csv = get_file_name("calculated", "csv", params.dataset.sample)
        calculated.to_csv(index=False, path_or_buf=tmp_dir / calculated_csv)
        if client:
            client.log_artifact(
                tmp_dir / calculated_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )
        else:
            log_artifact_local(
                tmp_dir / calculated_csv,
                f"{params.project_key}/models/inspections/{params.inspectionId}",
            )
    return websocket.Empty()


@websocket_actor(MLWorkerAction.runModelForDataFrame)
def run_model_for_data_frame(
    client: Optional[GiskardClient], params: websocket.RunModelForDataFrameParam, *args, **kwargs
) -> websocket.RunModelForDataFrame:
    model = BaseModel.download(client, params.model.project_key, params.model.id)
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
    elif model.is_text_generation:
        return websocket.RunModelForDataFrame(prediction=list(predictions.prediction.astype(str)))
    else:
        return websocket.RunModelForDataFrame(
            prediction=list(predictions.prediction.astype(str)),
            raw_prediction=list(predictions.prediction),
        )


@websocket_actor(MLWorkerAction.explain)
def explain_ws(client: Optional[GiskardClient], params: websocket.ExplainParam, *args, **kwargs) -> websocket.Explain:
    model = BaseModel.download(client, params.model.project_key, params.model.id)
    dataset = Dataset.download(client, params.dataset.project_key, params.dataset.id, params.dataset.sample)
    explanations = explain(model, dataset, params.columns)

    return websocket.Explain(
        explanations={str(k): websocket.Explanation(per_feature=v) for k, v in explanations["explanations"].items()}
    )


@websocket_actor(MLWorkerAction.explainText)
def explain_text_ws(
    client: Optional[GiskardClient], params: websocket.ExplainTextParam, *args, **kwargs
) -> websocket.ExplainText:
    model = BaseModel.download(client, params.model.project_key, params.model.id)
    text_column = params.feature_name

    if params.column_types[text_column] != "text":
        raise ValueError(f"Column {text_column} is not of type text")
    text_document = params.columns[text_column]
    input_df = pd.DataFrame({k: [v] for k, v in params.columns.items()})
    if model.meta.feature_names:
        input_df = input_df[model.meta.feature_names]
    (list_words, list_weights) = explain_text(model, input_df, text_column, text_document)
    # Classification model contains classification labels, but regression model does not
    classification_labels = model.meta.classification_labels if model.meta.classification_labels else ["WEIGHTS"]
    list_weights = list_weights if model.meta.classification_labels else [list_weights]
    map_features_weight = dict(zip(classification_labels, list_weights))
    return websocket.ExplainText(
        weights={
            str(k): websocket.WeightsPerFeature(weights=[weight for weight in map_features_weight[k]])
            for k in map_features_weight
        },
        words=list(list_words),
    )


@websocket_actor(MLWorkerAction.getCatalog)
def get_catalog(*args, **kwargs) -> websocket.Catalog:
    return websocket.Catalog(
        tests=map_function_meta_ws("TEST"),
        slices=map_dataset_process_function_meta_ws("SLICE"),
        transformations=map_dataset_process_function_meta_ws("TRANSFORMATION"),
    )


@websocket_actor(MLWorkerAction.datasetProcessing)
def dataset_processing(
    client: Optional[GiskardClient], params: websocket.DatasetProcessingParam, *args, **kwargs
) -> websocket.DatasetProcessing:
    dataset = Dataset.download(client, params.dataset.project_key, params.dataset.id, params.dataset.sample)

    for function in params.functions:
        arguments = parse_function_arguments(client, function.arguments)
        if function.slicingFunction:
            dataset.add_slicing_function(
                SlicingFunction.download(function.slicingFunction.id, client, function.slicingFunction.project_key)(
                    **arguments
                )
            )
        else:
            dataset.add_transformation_function(
                TransformationFunction.download(
                    function.transformationFunction.id, client, function.transformationFunction.project_key
                )(**arguments)
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
                modifications={key: str(value) for key, value in row[1].items() if not pd.isna(value)},
            )
            for row in modified_rows.iterrows()
        ],
    )


@websocket_actor(MLWorkerAction.runAdHocTest)
def run_ad_hoc_test(
    client: Optional[GiskardClient], params: websocket.RunAdHocTestParam, *args, **kwargs
) -> websocket.RunAdHocTest:
    test: GiskardTest = GiskardTest.download(params.testUuid, client, None)

    arguments = parse_function_arguments(client, params.arguments)

    arguments["debug"] = params.debug if params.debug else None
    debug_info = extract_debug_info(params.arguments) if params.debug else None

    test_result = do_run_adhoc_test(client, arguments, test, debug_info)

    return websocket.RunAdHocTest(
        results=[
            websocket.NamedSingleTestResult(
                testUuid=test.meta.uuid, result=map_result_to_single_test_result_ws(test_result)
            )
        ]
    )


@websocket_actor(MLWorkerAction.runTestSuite)
def run_test_suite(
    client: Optional[GiskardClient], params: websocket.TestSuiteParam, *args, **kwargs
) -> websocket.TestSuite:
    log_listener = LogListener()
    try:
        tests = [
            {
                "test": GiskardTest.download(t.testUuid, client, None),
                "arguments": parse_function_arguments(client, t.arguments),
                "id": t.id,
            }
            for t in params.tests
        ]

        global_arguments = parse_function_arguments(client, params.globalArguments)

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

        suite_result = suite.run(**global_arguments)

        identifier_single_test_results = []
        for identifier, result, arguments in suite_result.results:
            identifier_single_test_results.append(
                websocket.IdentifierSingleTestResult(
                    id=identifier,
                    result=map_result_to_single_test_result_ws(result),
                    arguments=function_argument_to_ws(arguments),
                )
            )

        return websocket.TestSuite(
            is_error=False,
            is_pass=suite_result.passed,
            results=identifier_single_test_results,
            logs=log_listener.close(),
        )

    except Exception as exc:
        logger.exception("An error occurred during the test suite execution: %s", exc)
        return websocket.TestSuite(is_error=True, is_pass=False, results=[], logs=log_listener.close())


@websocket_actor(MLWorkerAction.generateTestSuite)
def generate_test_suite(
    client: Optional[GiskardClient], params: websocket.GenerateTestSuiteParam, *args, **kwargs
) -> websocket.GenerateTestSuite:
    inputs = [map_suite_input_ws(i) for i in params.inputs]

    suite = Suite().generate_tests(inputs).to_dto(client, params.project_key)

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


@websocket_actor(MLWorkerAction.echo, execute_in_pool=False)
def echo(params: websocket.EchoMsg, *args, **kwargs) -> websocket.EchoMsg:
    return params


@websocket_actor(MLWorkerAction.getPush, timeout=30, ignore_timeout=True)
def get_push(
    client: Optional[GiskardClient], params: websocket.GetPushParam, *args, **kwargs
) -> websocket.GetPushResponse:
    object_uuid = ""
    object_params = {}
    project_key = params.model.project_key
    try:
        model = BaseModel.download(client, params.model.project_key, params.model.id)
        dataset = Dataset.download(client, params.dataset.project_key, params.dataset.id)

        df = pd.DataFrame.from_records([r.columns for r in params.dataframe.rows])
        if params.column_dtypes:
            for missing_column in [
                column_name for column_name in params.column_dtypes.keys() if column_name not in df.columns
            ]:
                df[missing_column] = np.nan
            df = Dataset.cast_column_to_dtypes(df, params.column_dtypes)

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

    # if df is empty, return early
    if df.empty:
        return

    from giskard.push.contribution import create_contribution_push
    from giskard.push.perturbation import create_perturbation_push
    from giskard.push.prediction import create_borderline_push, create_overconfidence_push

    contribs = create_contribution_push(model, dataset, df)
    perturbs = create_perturbation_push(model, dataset, df)
    overconf = create_overconfidence_push(model, dataset, df)
    borderl = create_borderline_push(model, dataset, df)

    contrib_ws = push_to_ws(contribs)
    perturb_ws = push_to_ws(perturbs)
    overconf_ws = push_to_ws(overconf)
    borderl_ws = push_to_ws(borderl)

    if params.cta_kind is not None and params.push_kind is not None:
        if params.push_kind == PushKind.PERTURBATION:
            push = perturbs
        elif params.push_kind == PushKind.CONTRIBUTION:
            push = contribs
        elif params.push_kind == PushKind.OVERCONFIDENCE:
            push = overconf
        elif params.push_kind == PushKind.BORDERLINE:
            push = borderl
        else:
            raise ValueError("Invalid push kind")

        logger.info("Handling push kind: " + str(params.push_kind) + " with cta kind: " + str(params.cta_kind))

        # Upload related object depending on CTA type
        if (
            params.cta_kind == CallToActionKind.CREATE_SLICE
            or params.cta_kind == CallToActionKind.CREATE_SLICE_OPEN_DEBUGGER
        ):
            push.slicing_function.meta.tags.append("generated")
            object_uuid = push.slicing_function.upload(client, project_key)
        if params.cta_kind == CallToActionKind.SAVE_PERTURBATION:
            for perturbation in push.transformation_function:
                object_uuid = perturbation.upload(client, project_key)
        if params.cta_kind == CallToActionKind.SAVE_EXAMPLE:
            object_uuid = push.saved_example.upload(client, project_key)
        if params.cta_kind == CallToActionKind.CREATE_TEST or params.cta_kind == CallToActionKind.ADD_TEST_TO_CATALOG:
            for test in push.tests:
                object_uuid = test.upload(client, project_key)
            # create empty dict
            object_params = {}
            # for every object in push.test_params, check if they're a subclass of Savable and if yes upload them
            for test_param_name in push.test_params:
                test_param = push.test_params[test_param_name]
                if isinstance(test_param, RegistryArtifact):
                    object_params[test_param_name] = test_param.upload(client, project_key)
                elif isinstance(test_param, Dataset):
                    object_params[test_param_name] = test_param.upload(client, project_key)
                else:
                    object_params[test_param_name] = test_param

        if object_uuid != "":
            logger.info(f"Uploaded object for CTA with uuid: {object_uuid}")

    if object_uuid != "":
        return websocket.GetPushResponse(
            contribution=contrib_ws,
            perturbation=perturb_ws,
            overconfidence=overconf_ws,
            borderline=borderl_ws,
            action=websocket.PushAction(object_uuid=object_uuid, arguments=function_argument_to_ws(object_params)),
        )

    return websocket.GetPushResponse(
        contribution=contrib_ws,
        perturbation=perturb_ws,
        overconfidence=overconf_ws,
        borderline=borderl_ws,
    )


def push_to_ws(push: Push):
    return push.to_ws() if push is not None else None
