import inspect
import logging
import re
import typing
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..utils.artifacts import serialize_parameter

try:
    from types import NoneType
except ImportError:
    # types.NoneType is only available from python >=3.10
    NoneType = type(None)
from typing import Optional, Dict, List, Union, Literal, TypeVar, Callable, Type, Any

logger = logging.getLogger(__name__)


class Kwargs:
    pass


def _get_plugin_method_full_name(func):
    from giskard.ml_worker.testing.registry.registry import plugins_root

    path_parts = list(Path(inspect.getfile(func)).relative_to(plugins_root).with_suffix("").parts)
    path_parts.insert(0, "giskard_plugins")
    if "__init__" in path_parts:
        path_parts.remove("__init__")
    path_parts.append(func.__name__)
    return ".".join(path_parts)


def create_test_function_id(func):
    try:
        from giskard.ml_worker.testing.registry.registry import plugins_root

        # is_relative_to is only available from python 3.9
        is_relative = Path(inspect.getfile(func)).relative_to(plugins_root)
    except ValueError:
        is_relative = False
    if is_relative:
        full_name = _get_plugin_method_full_name(func)
    else:
        full_name = f"{func.__module__}.{func.__name__}"
    return full_name


class SupportedModelTypes(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    TEXT_GENERATION = "text_generation"


ModelType = Union[SupportedModelTypes, Literal["classification", "regression", "text_generation"]]


class SupportedColumnTypes(Enum):
    NUMERIC = "numeric"
    CATEGORY = "category"
    TEXT = "text"


ColumnType = Union[SupportedColumnTypes, Literal["numeric", "category", "text"]]


class SavableMeta:
    uuid: Optional[str]

    def __init__(self, uuid: Optional[str] = None):
        self.uuid = uuid

    def to_json(self):
        return {"uuid": self.uuid}

    @classmethod
    def from_json(cls, json):
        obj = cls()
        obj.init_from_json(json)
        return obj

    def init_from_json(self, json: Dict[str, Any]):
        self.uuid = json["uuid"]


@dataclass
class ModelMeta:
    name: Optional[str]
    model_type: SupportedModelTypes
    feature_names: List[str]
    classification_labels: List[str]
    classification_threshold: float
    loader_module: str
    loader_class: str


@dataclass
class DatasetMeta:
    name: Optional[str]
    target: str
    column_types: Dict[str, str]
    column_dtypes: Dict[str, str]
    number_of_rows: int
    category_features: Dict[str, List[str]]


@dataclass
class FunctionArgument:
    name: str
    type: str
    default: any
    optional: bool
    argOrder: int


class CallableMeta(SavableMeta, ABC):
    code: str
    name: str
    display_name: str
    module: str
    doc: str
    module_doc: str
    tags: List[str]
    version: Optional[int]
    full_name: str
    type: str
    args: Dict[str, FunctionArgument]

    def __init__(
        self,
        callable_obj: Union[Callable, Type] = None,
        name: Optional[str] = None,
        tags: List[str] = None,
        version: Optional[int] = None,
        type: str = None,
    ):
        self.version = version
        self.type = type
        self.name = name
        self.tags = tags
        self.code = None
        self.display_name = None
        self.module = None
        self.doc = None
        self.module_doc = None
        self.full_name = None
        self.args = None

        if callable_obj:
            from giskard.ml_worker.testing.registry.registry import get_object_uuid

            self.full_name = create_test_function_id(callable_obj)
            func_uuid = get_object_uuid(callable_obj)
            super(CallableMeta, self).__init__(func_uuid)

            callable_obj.__module__.rpartition(".")
            func_doc = self.extract_doc(callable_obj)

            self.code = self.extract_code(callable_obj)
            self.name = callable_obj.__name__
            self.display_name = name or callable_obj.__name__
            self.module = callable_obj.__module__
            self.doc = func_doc
            self.module_doc = self.extract_module_doc(func_doc)
            self.tags = self.populate_tags(tags)

            parameters = self.extract_parameters(callable_obj)

            self.args = {
                parameter.name: FunctionArgument(
                    name=parameter.name,
                    type=extract_optional(parameter.annotation).__qualname__,
                    optional=parameter.default != inspect.Parameter.empty,
                    default=serialize_parameter(parameter.default),
                    argOrder=idx,
                )
                for idx, parameter in enumerate(parameters.values())
                if name != "self"
            }

    def extract_parameters(self, callable_obj):
        if inspect.isclass(callable_obj):
            parameters = list(inspect.signature(callable_obj.__init__).parameters.values())[1:]
        else:
            parameters = list(inspect.signature(callable_obj).parameters.values())

        return parameters

    @staticmethod
    def extract_module_doc(func_doc):
        return inspect.getmodule(func_doc).__doc__.strip() if inspect.getmodule(func_doc).__doc__ else None

    def populate_tags(self, tags=None):
        tags = [] if not tags else tags.copy()

        if self.name == "<lambda>":
            tags.append("lambda")
        elif self.full_name.partition(".")[0] == "giskard":
            tags.append("giskard")
        else:
            tags.append("custom")
        return tags

    def extract_code(self, callable_obj):
        code = None
        try:
            code = inspect.getsource(callable_obj)
        except Exception as e:
            logger.info(f"Failed to extract test function code {self.full_name}: %s" % e)
        return code

    @staticmethod
    def extract_doc(func):
        if func.__doc__:
            func_doc, _, args_doc = func.__doc__.partition("\n\n\n")
            func_doc = re.sub(r"\n[ \t\n]+", r"\n", func_doc.strip())
        else:
            func_doc = None
        return func_doc

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "display_name": self.display_name,
            "module": self.module,
            "doc": self.doc,
            "module_doc": self.module_doc,
            "code": self.code,
            "tags": self.tags,
            "type": self.type,
            "args": [
                {
                    "name": arg.name,
                    "type": arg.type,
                    "default": arg.default,
                    "optional": arg.optional,
                    "argOrder": arg.argOrder,
                }
                for arg in self.args.values()
            ]
            if self.args
            else None,
        }

    def init_from_json(self, json: Dict[str, Any]):
        super().init_from_json(json)
        self.name = json["name"]
        self.display_name = json["displayName"]
        self.module = json["module"]
        self.doc = json["doc"]
        self.module_doc = json["moduleDoc"]
        self.code = json["code"]
        self.tags = json["tags"]
        self.version = json["version"]
        self.type = json["type"]
        self.args = (
            {
                arg["name"]: FunctionArgument(
                    name=arg["name"],
                    type=arg["type"],
                    default=arg["defaultValue"],
                    optional=arg["optional"],
                    argOrder=arg["argOrder"],
                )
                for arg in json["args"]
            }
            if json["args"]
            else None
        )


def __repr__(self) -> str:
    return f"CallableMeta: {self.module}.{self.name}"


class TestFunctionMeta(CallableMeta):
    debug_description: str

    def __init__(
        self,
        callable_obj: Union[Callable, Type] = None,
        name: Optional[str] = None,
        tags: List[str] = None,
        debug_description: str = None,
        version: Optional[int] = None,
        type: str = None,
    ):
        super().__init__(callable_obj, name, tags, version, type)
        self.debug_description = debug_description

    def extract_parameters(self, callable_obj):
        parameters = unknown_annotations_to_kwargs(CallableMeta.extract_parameters(self, callable_obj))

        return {p.name: p for p in parameters}

    def to_json(self):
        json = super().to_json()
        return {
            **json,
            "debug_description": self.debug_description,
        }

    def init_from_json(self, json: Dict[str, Any]):
        super().init_from_json(json)
        self.debug_description = json["debug_description"] if "debug_description" in json.keys() else None


class DatasetProcessFunctionType(Enum):
    CLAUSES = "CLAUSES"
    CODE = "CODE"


class DatasetProcessFunctionMeta(CallableMeta):
    cell_level: bool
    column_type: Optional[str]
    process_type: DatasetProcessFunctionType
    clauses: Optional[List[Dict[str, Any]]]

    def __init__(
        self,
        callable_obj: Union[Callable, Type] = None,
        name: Optional[str] = None,
        tags: List[str] = None,
        version: Optional[int] = None,
        type: str = None,
        process_type: DatasetProcessFunctionType = DatasetProcessFunctionType.CODE,
        cell_level: bool = False,
        clauses: Optional[List[Dict[str, Any]]] = None,
    ):
        super(DatasetProcessFunctionMeta, self).__init__(callable_obj, name, tags, version, type)
        self.cell_level = cell_level
        self.process_type = process_type
        self.clauses = clauses

        if cell_level:
            if inspect.isclass(callable_obj):
                parameters = list(inspect.signature(callable_obj.__init__).parameters.values())[1:]
            else:
                parameters = list(inspect.signature(callable_obj).parameters.values())
            self.column_type = parameters[0].annotation.__qualname__
        else:
            self.column_type = None

    def extract_parameters(self, callable_obj):
        parameters = unknown_annotations_to_kwargs(CallableMeta.extract_parameters(self, callable_obj)[1:])

        return {p.name: p for p in parameters}

    def to_json(self):
        json = super().to_json()
        return {
            **json,
            "cellLevel": self.cell_level,
            "columnType": self.column_type,
            "processType": self.process_type.value,
            "clauses": self.clauses,
        }

    def init_from_json(self, json: Dict[str, Any]):
        super().init_from_json(json)
        self.cell_level = json["cellLevel"]
        self.column_type = json["columnType"]
        self.process_type = DatasetProcessFunctionType[json["processType"]]
        self.clauses = json["clauses"]


DT = TypeVar("DT")
SMT = TypeVar("SMT", bound=SavableMeta)


def unknown_annotations_to_kwargs(parameters: List[inspect.Parameter]) -> List[inspect.Parameter]:
    from giskard.models.base import BaseModel
    from giskard.datasets.base import Dataset
    from giskard.ml_worker.testing.registry.slicing_function import SlicingFunction
    from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction

    allowed_types = [str, bool, int, float, BaseModel, Dataset, SlicingFunction, TransformationFunction]
    allowed_types = allowed_types + list(map(lambda x: Optional[x], allowed_types))

    has_kwargs = any(
        [param for param in parameters if not any([param.annotation == allowed_type for allowed_type in allowed_types])]
    )

    parameters = [
        param for param in parameters if any([param.annotation == allowed_type for allowed_type in allowed_types])
    ]

    if has_kwargs:
        parameters.append(inspect.Parameter(name="kwargs", kind=4, annotation=Kwargs))

    return parameters


def extract_optional(field):
    if typing.get_origin(field) is Union and NoneType in typing.get_args(field):
        return Union[tuple([arg for arg in typing.get_args(field) if arg is not None and arg is not NoneType])]
    else:
        return field


class ComparisonType(Enum):
    IS = "IS"
    IS_NOT = "IS_NOT"
    CONTAINS = "CONTAINS"
    DOES_NOT_CONTAINS = "DOES_NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    IS_EMPTY = "IS_EMPTY"
    IS_NOT_EMPTY = "IS_NOT_EMPTY"


@dataclass
class ComparisonClauseDTO:
    columnName: str
    comparisonType: ComparisonType
    columnDtype: str
    value: Optional[str]
