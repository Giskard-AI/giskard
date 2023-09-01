import logging
import os
import posixpath
import shutil
from pathlib import Path
from typing import List, Dict, Any

from mlflow.store.artifact.artifact_repo import verify_artifact_path

from giskard.core.suite import ModelInput, DatasetInput, SuiteInput
from giskard.datasets.base import Dataset
from giskard.ml_worker import websocket
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.ml_worker import MLWorker
from giskard.ml_worker.testing.registry.registry import tests_registry
from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
from giskard.ml_worker.testing.registry.transformation_function import (
    TransformationFunction,
)
from giskard.ml_worker.testing.test_result import TestResult, TestMessageLevel
from giskard.ml_worker.websocket import (
    EchoMsg,
    ExplainParam,
    GetInfoParam,
    RunModelParam,
    TestSuiteParam,
    ExplainTextParam,
    RunAdHocTestParam,
    DatasetProcessingParam,
    GenerateTestSuiteParam,
    RunModelForDataFrameParam, GetPushParam,
)
from giskard.ml_worker.websocket.action import MLWorkerAction
from giskard.models.base import BaseModel
from giskard.path_utils import projects_dir

logger = logging.getLogger(__name__)


def parse_action_param(action, params):
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
    elif action == MLWorkerAction.generateTestSuite:
        return GenerateTestSuiteParam.parse_obj(params)
    elif action == MLWorkerAction.getPush:
        return GetPushParam.parse_obj(params)
    return params


def fragment_message(payload: str, frag_i: int, frag_length: int):
    return payload[frag_i * frag_length: min((frag_i + 1) * frag_length, len(payload))]


def extract_debug_info(request_arguments):
    template_info = " | <xxx:xxx_id>"
    info = {"suffix": "", "project_key": ""}
    for arg in request_arguments:
        if arg.model:
            filled_info = template_info.replace("xxx", arg.name)
            info["suffix"] += filled_info.replace(arg.name + "_id", arg.model.id)
            info["project_key"] = arg.model.project_key  # in case model is in the args and dataset is not
        elif arg.dataset:
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


def parse_function_arguments(ml_worker: MLWorker, request_arguments: List[websocket.FuncArgument]):
    arguments = dict()

    # Processing empty list
    if not request_arguments:
        return arguments

    for arg in request_arguments:
        if arg.is_none:
            continue
        if arg.dataset is not None:
            arguments[arg.name] = Dataset.download(
                ml_worker.client,
                arg.dataset.project_key,
                arg.dataset.id,
                arg.dataset.sample,
            )
        elif arg.model is not None:
            arguments[arg.name] = BaseModel.download(ml_worker.client, arg.model.project_key, arg.model.id)
        elif arg.slicingFunction is not None:
            arguments[arg.name] = SlicingFunction.download(arg.slicingFunction.id, ml_worker.client, None)(
                **parse_function_arguments(ml_worker, arg.args)
            )
        elif arg.transformationFunction is not None:
            arguments[arg.name] = TransformationFunction.download(
                arg.transformationFunction.id, ml_worker.client, None
            )(**parse_function_arguments(ml_worker, arg.args))
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
            arguments.update(kwargs)
        else:
            raise IllegalArgumentError("Unknown argument type")
    return arguments


def map_result_to_single_test_result_ws(result) -> websocket.SingleTestResult:
    if isinstance(result, TestResult):
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
            output_df=None,
            number_of_perturbed_rows=result.number_of_perturbed_rows,
            actual_slices_size=result.actual_slices_size,
            reference_slices_size=result.reference_slices_size,
            output_df_id=result.output_df_id,
        )
    elif isinstance(result, bool):
        return websocket.SingleTestResult(passed=result)
    else:
        raise ValueError("Result of test can only be 'TestResult' or 'bool'")


def do_run_adhoc_test(client, arguments, test, debug_info=None):
    logger.info(f"Executing {test.meta.display_name or f'{test.meta.module}.{test.meta.name}'}")
    test_result = test.get_builder()(**arguments).execute()
    if test_result.output_df is not None:  # i.e. if debug is True and test has failed

        if debug_info is None:
            raise ValueError(
                "You have requested to debug the test, "
                + "but extract_debug_info did not return the information needed."
            )

        test_result.output_df.name += debug_info["suffix"]

        test_result.output_df_id = test_result.output_df.upload(client=client, project_key=debug_info["project_key"])
        # We won't return output_df from WS, rather upload it
        test_result.output_df = None
    elif arguments["debug"]:
        raise ValueError(
            "This test does not return any examples to debug. "
            "Check the debugging method associated to this test at "
            "https://docs.giskard.ai/en/latest/reference/tests/index.html"
        )

    return test_result


def map_suite_input_ws(i: websocket.SuiteInput):
    if i.type == "Model" and i.model_meta is not None:
        return ModelInput(i.name, i.model_meta.model_type)
    elif i.type == "Dataset" and i.dataset_meta is not None:
        return DatasetInput(i.name, i.dataset_meta.target)
    else:
        return SuiteInput(i.name, i.type)


def function_argument_to_ws(value: Dict[str, Any]):
    args = list()

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
        #     arguments[arg.name] = SlicingFunction.load(arg.slicingFunction.id, self.client, None)(
        #         **self.parse_function_arguments(arg.args))
        elif isinstance(obj, TransformationFunction):
            funcargs = websocket.FuncArgument(
                name=v,
                transformationFunction=websocket.ArtifactRef(project_key="test", id=str(obj.meta.uuid)),
                args=function_argument_to_ws(obj.params),
                none=False,
            )
        #     arguments[arg.name] = TransformationFunction.load(arg.transformationFunction.id, self.client, None)(
        #         **self.parse_function_arguments(arg.args))
        elif isinstance(obj, float):
            funcargs = websocket.FuncArgument(name=v, float=obj, none=False)
        elif isinstance(obj, int):
            funcargs = websocket.FuncArgument(name=v, int=obj, none=False)
        elif isinstance(obj, str):
            funcargs = websocket.FuncArgument(name=v, str=obj, none=False)
        elif isinstance(obj, bool):
            funcargs = websocket.FuncArgument(name=v, bool=obj, none=False)
        elif isinstance(obj, dict):
            funcargs = websocket.FuncArgument(name=v, kwargs=str(obj), none=False)
        else:
            raise IllegalArgumentError("Unknown argument type")
        args.append(funcargs)

    return args
