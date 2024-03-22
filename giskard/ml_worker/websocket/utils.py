from typing import Any, Callable, Dict, List, Optional

import logging
import uuid
from collections import defaultdict

import pandas as pd

from giskard.client.giskard_client import GiskardClient
from giskard.core.suite import DatasetInput, ModelInput, SuiteInput
from giskard.core.test_result import TestMessageLevel, TestResult
from giskard.datasets.base import Dataset
from giskard.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker import websocket
from giskard.ml_worker.websocket import (
    AbortParams,
    CreateDatasetParam,
    CreateSubDatasetParam,
    DatasetProcessingParam,
    Documentation,
    EchoMsg,
    ExplainParam,
    ExplainTextParam,
    GetInfoParam,
    GetLogsParams,
    GetPushParam,
    RunAdHocTestParam,
    RunModelForDataFrameParam,
    RunModelParam,
    TestSuiteParam,
)
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.models.base import BaseModel
from giskard.registry.registry import tests_registry
from giskard.registry.slicing_function import SlicingFunction
from giskard.registry.transformation_function import TransformationFunction

logger = logging.getLogger(__name__)


def parse_action_param(action: MLWorkerAction, params):
    # TODO: Sort by usage frequency from future MixPanel metrics #NOSONAR
    if action == MLWorkerAction.abort:
        return AbortParams.parse_obj(params)
    if action == MLWorkerAction.getInfo:
        return GetInfoParam.parse_obj(params)
    elif action == MLWorkerAction.runAdHocTest:
        return RunAdHocTestParam.parse_obj(params)
    elif action == MLWorkerAction.datasetProcessing:
        return DatasetProcessingParam.parse_obj(params)
    elif action == MLWorkerAction.runTestSuite:
        return TestSuiteParam.parse_obj(params)
    elif action == MLWorkerAction.runModel:
        return RunModelParam.parse_obj(params)
    elif action == MLWorkerAction.runModelForDataFrame:
        return RunModelForDataFrameParam.parse_obj(params)
    elif action == MLWorkerAction.explain:
        return ExplainParam.parse_obj(params)
    elif action == MLWorkerAction.explainText:
        return ExplainTextParam.parse_obj(params)
    elif action == MLWorkerAction.echo:
        return EchoMsg.parse_obj(params)
    elif action == MLWorkerAction.getPush:
        return GetPushParam.parse_obj(params)
    elif action == MLWorkerAction.createSubDataset:
        return CreateSubDatasetParam.parse_obj(params)
    elif action == MLWorkerAction.createDataset:
        return CreateDatasetParam.parse_obj(params)
    elif action == MLWorkerAction.getLogs:
        return GetLogsParams.parse_obj(params)
    return params


def fragment_message(payload: str, frag_i: int, frag_length: int):
    return payload[frag_i * frag_length : min((frag_i + 1) * frag_length, len(payload))]


def extract_debug_info(request_arguments):
    template_info = " | <xxx:xxx_id>"
    info = {"suffix": "", "project_key": "", "datasets": dict()}
    for arg in request_arguments:
        if arg.model:
            filled_info = template_info.replace("xxx", arg.name)
            info["suffix"] += filled_info.replace(arg.name + "_id", arg.model.id)
            info["project_key"] = arg.model.project_key  # in case model is in the args and dataset is not
        elif arg.dataset:
            info["datasets"][arg.dataset.id] = arg.dataset  # retrieve the dataset info
            filled_info = template_info.replace("xxx", arg.name)
            info["suffix"] += filled_info.replace(arg.name + "_id", arg.dataset.id)
            info["project_key"] = arg.dataset.project_key  # in case dataset is in the args and model is not
    return info


def map_function_meta_ws(callable_type):
    return {
        test.uuid: websocket.FunctionMeta(
            uuid=test.uuid,
            name=test.name,
            displayName=test.display_name,
            module=test.module,
            doc=None
            if test.doc is None
            else Documentation(description=test.doc.description, parameters=test.doc.parameters),
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
                for a in (test.args.values() if test.args else [])  # args could be None
            ],
            debugDescription=test.debug_description,
        )
        for test in tests_registry.get_all().values()
        if test.type == callable_type and "giskard" in test.tags
    }


def map_dataset_process_function_meta_ws(callable_type):
    return {
        test.uuid: websocket.DatasetProcessFunctionMeta(
            uuid=test.uuid,
            name=test.name,
            displayName=test.display_name,
            module=test.module,
            doc=None
            if test.doc is None
            else Documentation(description=test.doc.description, parameters=test.doc.parameters),
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
                for a in (test.args.values() if test.args else [])  # args could be None
            ],
            cellLevel=test.cell_level,
            columnType=test.column_type,
            processType=test.process_type.name,
        )
        for test in tests_registry.get_all().values()
        if test.type == callable_type and "giskard" in test.tags
    }


def _get_or_load(loaded_artifacts: Dict[str, Dict[str, Any]], type: str, uuid: str, load_fn: Callable[[], Any]) -> Any:
    if uuid not in loaded_artifacts[type]:
        loaded_artifacts[type][uuid] = load_fn()

    return loaded_artifacts[type][uuid]


def parse_function_arguments(
    client: GiskardClient,
    request_arguments: List[websocket.FuncArgument],
    loaded_artifacts: Optional[Dict[str, Dict[str, Any]]] = None,
):
    if loaded_artifacts is None:
        loaded_artifacts = defaultdict(dict)

    arguments = dict()

    # Processing empty list
    if not request_arguments:
        return arguments

    for arg in request_arguments:
        if arg.is_none:
            continue
        if arg.dataset is not None:
            arguments[arg.name] = _get_or_load(
                loaded_artifacts,
                "Dataset",
                arg.dataset.id,
                lambda: Dataset.download(
                    client,
                    arg.dataset.project_key,
                    arg.dataset.id,
                    arg.dataset.sample,
                ),
            )
        elif arg.model is not None:
            arguments[arg.name] = _get_or_load(
                loaded_artifacts,
                "BaseModel",
                arg.model.id,
                lambda: BaseModel.download(client, arg.model.project_key, arg.model.id),
            )
        elif arg.slicingFunction is not None:
            arguments[arg.name] = SlicingFunction.download(
                arg.slicingFunction.id, client, arg.slicingFunction.project_key
            )(**parse_function_arguments(client, arg.args, loaded_artifacts))
        elif arg.transformationFunction is not None:
            arguments[arg.name] = TransformationFunction.download(
                arg.transformationFunction.id, client, arg.transformationFunction.project_key
            )(**parse_function_arguments(client, arg.args, loaded_artifacts))
        elif arg.float_arg is not None:
            arguments[arg.name] = float(arg.float_arg)
        elif arg.int_arg is not None:
            arguments[arg.name] = int(arg.int_arg)
        elif arg.str_arg is not None:
            arguments[arg.name] = str(arg.str_arg)
        elif arg.bool_arg is not None:
            arguments[arg.name] = bool(arg.bool_arg)
        elif arg.kwargs is not None:
            kwargs = dict()
            exec(arg.kwargs, {"kwargs": kwargs})
            arguments[arg.name] = kwargs
        else:
            raise IllegalArgumentError("Unknown argument type")
    return arguments


def map_result_to_single_test_result_ws(
    result,
    datasets: Dict[uuid.UUID, Dataset],
    client: GiskardClient,
    project_key: Optional[str] = None,
) -> websocket.SingleTestResult:
    if isinstance(result, TestResult):
        result.output_ds = result.output_ds or []

        if result.output_df is not None:
            _upload_generated_output_df(client, datasets, project_key, result)

        return websocket.SingleTestResult(
            passed=bool(result.passed),
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
            metric_name=result.metric_name,
            failed_indexes={
                str(dataset.original_id): list(datasets[dataset.original_id].df.index.get_indexer_for(dataset.df.index))
                for dataset in result.output_ds
            },
            details=None
            if not result.details
            else websocket.SingleTestResultDetails(
                inputs=result.details.inputs,
                outputs=result.details.outputs,
                results=result.details.results,
                metadata=result.details.metadata,
            ),
        )
    elif isinstance(result, bool):
        return websocket.SingleTestResult(passed=result)
    else:
        raise ValueError("Result of test can only be 'TestResult' or 'bool'")


def _upload_generated_output_df(client, datasets, project_key, result):
    if not isinstance(result.output_df, Dataset):
        raise ValueError("The test result `output_df` provided must be a dataset instance")

    logger.warning(
        """
    Your using legacy test debugging though `output_df`. This feature will be removed in the future.
    Please migrate to `output_ds`.
    """
    )

    if result.output_df.original_id not in datasets.keys():
        if not project_key:
            raise ValueError("Unable to upload debug dataset due to missing `project_key`")

        result.output_df.upload(client, project_key)

    datasets[result.output_df.original_id] = result.output_df
    result.output_ds.append(result.output_df)


def do_run_adhoc_test(arguments, test):
    logger.info(f"Executing {test.meta.display_name or f'{test.meta.module}.{test.meta.name}'}")
    return test(**arguments).execute()


def map_suite_input_ws(i: websocket.SuiteInput):
    if i.type == "Model" and i.model_meta is not None:
        return ModelInput(i.name, i.model_meta.model_type)
    elif i.type == "Dataset" and i.dataset_meta is not None:
        return DatasetInput(i.name, i.dataset_meta.target)
    else:
        return SuiteInput(i.name, i.type)


def function_argument_to_ws(value: Dict[str, Any]):
    args = list()
    kwargs = dict()

    for v in value:
        obj = value[v]
        if isinstance(obj, Dataset):
            funcargs = websocket.FuncArgument(
                name=v, dataset=websocket.ArtifactRef(project_key="test", id=str(obj.id)), none=False
            )
        elif isinstance(obj, BaseModel):
            funcargs = websocket.FuncArgument(
                name=v, model=websocket.ArtifactRef(project_key="test", id=str(obj.id)), none=False
            )
        elif isinstance(obj, SlicingFunction):
            funcargs = websocket.FuncArgument(
                name=v,
                slicingFunction=websocket.ArtifactRef(project_key="test", id=str(obj.meta.uuid)),
                args=function_argument_to_ws(obj.params),
                none=False,
            )
        elif isinstance(obj, TransformationFunction):
            funcargs = websocket.FuncArgument(
                name=v,
                transformationFunction=websocket.ArtifactRef(project_key="test", id=str(obj.meta.uuid)),
                args=function_argument_to_ws(obj.params),
                none=False,
            )
        elif isinstance(obj, float):
            funcargs = websocket.FuncArgument(name=v, float=obj, none=False)
        elif isinstance(obj, int) and not isinstance(obj, bool):  # Avoid bool being considered as int
            funcargs = websocket.FuncArgument(name=v, int=obj, none=False)
        elif isinstance(obj, str):
            funcargs = websocket.FuncArgument(name=v, str=obj, none=False)
        elif isinstance(obj, bool):
            funcargs = websocket.FuncArgument(name=v, bool=obj, none=False)
        else:
            kwargs[v] = obj
            continue
        args.append(funcargs)

    if len(kwargs) > 0:
        args.append(
            websocket.FuncArgument(
                name="kwargs",
                kwargs="\n".join([f"kwargs[{repr(key)}] = {repr(value)}" for key, value in kwargs.items()]),
                none=False,
            )
        )

    return args


def do_create_sub_dataset(datasets: Dict[str, Dataset], name: Optional[str], row_indexes: Dict[str, List[int]]):
    # TODO: validate all dataset have same target and column types before
    dataset_list = list(datasets.values())

    return Dataset(
        df=pd.concat([dataset.df.iloc[row_indexes[dataset_id]] for dataset_id, dataset in datasets.items()]),
        name=name,
        target=dataset_list[0].target,
        cat_columns=dataset_list[0].cat_columns,
        column_types=dataset_list[0].column_types,
        validation=False,
    )


def do_create_dataset(name: Optional[str], headers: List[str], rows: List[List[str]]):
    return Dataset(pd.DataFrame(rows, columns=headers), name=name, validation=False)
