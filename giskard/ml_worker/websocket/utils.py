import logging
import os
import shutil
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd
from mlflow.store.artifact.artifact_repo import verify_artifact_path

from giskard.client.giskard_client import GiskardClient
from giskard.core.suite import DatasetInput, ModelInput, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker import websocket
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.testing.registry.registry import tests_registry
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
from giskard.ml_worker.testing.test_result import TestMessageLevel, TestResult
from giskard.ml_worker.websocket import (
    CreateSubDatasetParam,
    DatasetProcessingParam,
    EchoMsg,
    ExplainParam,
    ExplainTextParam,
    GetInfoParam,
    GetPushParam,
    RunAdHocTestParam,
    RunModelForDataFrameParam,
    RunModelParam,
    TestSuiteParam,
)
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.models.base import BaseModel
from giskard.path_utils import projects_dir

logger = logging.getLogger(__name__)


def parse_action_param(action: MLWorkerAction, params):
    # TODO: Sort by usage frequency from future MixPanel metrics #NOSONAR
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
                for a in (test.args.values() if test.args else [])  # args could be None
            ],
            debugDescription=test.debug_description,
        )
        for test in tests_registry.get_all().values()
        if test.type == callable_type and "giskard" in test.tags
    }


def log_artifact_local(local_file, artifact_path=None):
    # Log artifact locally from an internal worker
    verify_artifact_path(artifact_path)

    file_name = os.path.basename(local_file)

    if artifact_path:
        artifact_file = projects_dir / artifact_path / file_name
    else:
        artifact_file = projects_dir / file_name
    artifact_file.parent.mkdir(parents=True, exist_ok=True)

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
                for a in (test.args.values() if test.args else [])  # args could be None
            ],
            cellLevel=test.cell_level,
            columnType=test.column_type,
            processType=test.process_type.name,
        )
        for test in tests_registry.get_all().values()
        if test.type == callable_type and "giskard" in test.tags
    }


def parse_function_arguments(client: Optional[GiskardClient], request_arguments: List[websocket.FuncArgument]):
    arguments = dict()

    # Processing empty list
    if not request_arguments:
        return arguments

    for arg in request_arguments:
        if arg.is_none:
            continue
        if arg.dataset is not None:
            arguments[arg.name] = Dataset.download(
                client,
                arg.dataset.project_key,
                arg.dataset.id,
                arg.dataset.sample,
            )
        elif arg.model is not None:
            arguments[arg.name] = BaseModel.download(client, arg.model.project_key, arg.model.id)
        elif arg.slicingFunction is not None:
            arguments[arg.name] = SlicingFunction.download(
                arg.slicingFunction.id, client, arg.slicingFunction.project_key
            )(**parse_function_arguments(client, arg.args))
        elif arg.transformationFunction is not None:
            arguments[arg.name] = TransformationFunction.download(
                arg.transformationFunction.id, client, arg.transformationFunction.project_key
            )(**parse_function_arguments(client, arg.args))
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
    client: Optional[GiskardClient] = None,
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
            number_of_perturbed_rows=result.number_of_perturbed_rows,
            actual_slices_size=result.actual_slices_size,
            reference_slices_size=result.reference_slices_size,
            failed_indexes={
                str(dataset.original_id): list(datasets[dataset.original_id].df.index.get_indexer_for(dataset.df.index))
                for dataset in result.output_ds
            },
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
        if not client:
            raise RuntimeError("Legacy test debugging using `output_df` is not supported internal ML worker")

        if not project_key:
            raise ValueError("Unable to upload debug dataset due to missing `project_key`")

        result.output_df.upload(client, project_key)

    datasets[result.output_df.original_id] = result.output_df
    result.output_ds.append(result.output_df)


def do_run_adhoc_test(arguments, test):
    logger.info(f"Executing {test.meta.display_name or f'{test.meta.module}.{test.meta.name}'}")
    return test.get_builder()(**arguments).execute()


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
