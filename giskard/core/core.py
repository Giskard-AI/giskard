import typing

import functools
import inspect
import logging
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from griffe import Docstring
from griffe.docstrings.dataclasses import (
    DocstringSection,
    DocstringSectionParameters,
    DocstringSectionReturns,
)
from griffe.enumerations import DocstringSectionKind

from ..utils.artifacts import serialize_parameter

try:
    from types import NoneType
except ImportError:
    # types.NoneType is only available from python >=3.10
    NoneType = type(None)
from typing import Any, Callable, Dict, List, Literal, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)
DEMILITER = f"\n{'='*20}\n"


class Kwargs:
    pass


_T = TypeVar("_T")


# Sentinel class used until PEP 0661 is accepted
class NotGiven:
    """
    A sentinel singleton class used to distinguish omitted keyword arguments
    from those passed in with the value None (which may have different behavior).

    For example:

    ```py
    def get(timeout: Union[int, NotGiven, None] = NotGiven()) -> Response: ...

    get(timout=1) # 1s timeout
    get(timout=None) # No timeout
    get() # Default timeout behavior, which may not be statically known at the method definition.
    ```
    """

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NotGivenOr = Union[_T, NotGiven]
NOT_GIVEN = NotGiven()


def _get_plugin_method_full_name(func):
    from giskard.registry.registry import plugins_root

    path_parts = list(Path(inspect.getfile(func)).relative_to(plugins_root).with_suffix("").parts)
    path_parts.insert(0, "giskard_plugins")
    if "__init__" in path_parts:
        path_parts.remove("__init__")
    path_parts.append(func.__name__)
    return ".".join(path_parts)


def create_test_function_id(func):
    from giskard.registry.registry import plugins_root

    is_relative = Path(inspect.getfile(func)).is_relative_to(plugins_root)
    if is_relative:
        full_name = _get_plugin_method_full_name(func)
    else:
        full_name = f"{func.__module__}.{func.__name__}"
    return full_name


class SupportedModelTypes(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    TEXT_GENERATION = "text_generation"


ModelType = Union[SupportedModelTypes, Literal["classification", "regression", "text_generation"]]


class SupportedColumnTypes(str, Enum):
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
    description: Optional[str]
    model_type: SupportedModelTypes
    feature_names: List[str]
    classification_labels: List[str]
    classification_threshold: float
    loader_module: str
    loader_class: str


@dataclass
class DatasetMeta:
    name: Optional[str]
    target: Optional[str]
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


class CallableDocumentation:
    description: Optional[str]
    parameters: Optional[Dict[str, str]]

    def __init__(self, description: Optional[str] = None, parameters: Optional[Dict[str, str]] = None):
        self.description = description
        self.parameters = parameters

    def to_dict(self):
        return {
            "description": self.description,
            "parameters": self.parameters,
        }


class CallableMeta(SavableMeta, ABC):
    callable_obj: Union[Callable, Type]
    code: str
    name: str
    display_name: str
    module: str

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
        self.callable_obj = callable_obj
        self.version = version
        self.type = type
        self.name = name
        self.tags = tags
        self.code = None
        self.display_name = None
        self.module = None
        self.module_doc = None
        self.full_name = None
        self.args = None

        if callable_obj:
            from giskard.registry.registry import get_object_uuid

            self.full_name = create_test_function_id(callable_obj)
            func_uuid = get_object_uuid(callable_obj)
            super(CallableMeta, self).__init__(func_uuid)

            callable_obj.__module__.rpartition(".")

            self.code = self.extract_code(callable_obj)
            self.name = callable_obj.__name__
            self.display_name = name or callable_obj.__name__
            self.module = callable_obj.__module__
            self.module_doc = self.extract_module_doc(callable_obj)
            self.tags = self.populate_tags(tags)

            parameters = self.extract_parameters(callable_obj)
            for param in parameters:
                param.default = serialize_parameter(param.default)

            self.args = {param.name: param for param in parameters}

    @functools.cached_property
    def doc(self) -> Optional[CallableDocumentation]:
        return self.extract_doc(self.callable_obj) if self.callable_obj else None

    def extract_parameters(self, callable_obj) -> List[FunctionArgument]:
        if inspect.isclass(callable_obj):
            parameters = list(inspect.signature(callable_obj.__init__).parameters.values())[1:]
        else:
            parameters = list(inspect.signature(callable_obj).parameters.values())

        return [
            FunctionArgument(
                name=parameter.name,
                type=self.extract_parameter_type_name(parameter),
                optional=parameter.default != inspect.Parameter.empty,
                default=parameter.default,
                argOrder=idx,
            )
            for idx, parameter in enumerate(parameters)
        ]

    @staticmethod
    def extract_parameter_type_name(parameter):
        return (
            extract_optional(parameter.annotation).__qualname__
            if hasattr(extract_optional(parameter.annotation), "__qualname__")
            else None
        )

    @staticmethod
    def extract_module_doc(obj):
        return inspect.getmodule(obj).__doc__.strip() if inspect.getmodule(obj).__doc__ else None

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
    def default_doc(description: str) -> CallableDocumentation:
        doc = CallableDocumentation()
        doc.description = description
        doc.parameters = {}
        return doc

    @staticmethod
    def extract_doc(func) -> Optional[CallableDocumentation]:
        if not func.__doc__:
            return None

        res: CallableDocumentation = CallableDocumentation()

        parsed_docs: List[List[DocstringSection]] = list(
            sorted(
                [Docstring(func.__doc__).parse(parser) for parser in ["numpy", "google", "sphinx"]],
                key=len,
                reverse=True,
            )
        )

        best_doc: List[DocstringSection] = parsed_docs[0]  # We keep the one with most sections
        res.parameters = {}
        for d in best_doc:
            if d.kind == DocstringSectionKind.text:
                description_value: str = d.value.strip()
                if res.description and description_value.startswith("References"):
                    res.description += "\n\n"
                    res.description += description_value.replace("\n----------\n", "\n")
                elif res.description:
                    logger.warning(
                        f"{func.__name__} with already initialized description: {DEMILITER}{res.description}{DEMILITER} is being overwritten by {DEMILITER}{description_value}{DEMILITER}"
                    )
                res.description = description_value
            elif d.kind == DocstringSectionKind.parameters:
                params: DocstringSectionParameters = d
                missing_annotation = [p.name for p in params.value if p.annotation is None]
                if len(missing_annotation) > 0:
                    logger.warning(
                        f"{func.__name__} is missing type hinting for params {', '.join(missing_annotation)}"
                    )

                res.parameters = {p.name: p.description.strip() for p in params.value}
            elif d.kind == DocstringSectionKind.returns:
                returns: DocstringSectionReturns = d
                missing_annotation = [p.name for p in returns.value if p.annotation is None]
                if len(missing_annotation) > 0:
                    logger.warning(
                        f"{func.__name__} is missing type hinting for return elt {', '.join(missing_annotation)}"
                    )
            else:
                logger.warning(f"Unexpected documentation element for {func.__name__}: {d.kind}")

        return res

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "display_name": self.display_name,
            "module": self.module,
            "doc": self.doc.to_dict() if self.doc else None,
            "module_doc": self.module_doc,
            "code": self.code,
            "tags": self.tags,
            "type": self.type,
            "args": (
                [
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
                else None
            ),
        }

    def init_from_json(self, json: Dict[str, Any]):
        super().init_from_json(json)
        self.name = json["name"]
        self.display_name = json["displayName"]
        self.module = json["module"]
        self.doc = (
            CallableDocumentation(
                description=json["doc"]["description"],
                parameters=json["doc"]["parameters"],
            )
            if json["doc"]
            else None
        )
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

    def extract_parameters(self, callable_obj) -> List[FunctionArgument]:
        return unknown_annotations_to_kwargs(CallableMeta.extract_parameters(self, callable_obj))

    def to_json(self):
        json = super().to_json()
        return {
            **json,
            "debug_description": self.debug_description,
        }

    def init_from_json(self, json: Dict[str, Any]):
        super().init_from_json(json)
        self.debug_description = json["debug_description"] if "debug_description" in json.keys() else None


class DatasetProcessFunctionType(str, Enum):
    CLAUSES = "CLAUSES"
    CODE = "CODE"


class DatasetProcessFunctionMeta(CallableMeta):
    cell_level: bool
    column_type: Optional[str]
    process_type: DatasetProcessFunctionType
    clauses: List[Dict[str, Any]]

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
        self.clauses = clauses or list()

        if cell_level:
            if inspect.isclass(callable_obj):
                parameters = list(inspect.signature(callable_obj.__init__).parameters.values())[1:]
            else:
                parameters = list(inspect.signature(callable_obj).parameters.values())
            self.column_type = parameters[0].annotation.__qualname__
        else:
            self.column_type = None

    def extract_parameters(self, callable_obj) -> List[FunctionArgument]:
        return unknown_annotations_to_kwargs(CallableMeta.extract_parameters(self, callable_obj)[1:])

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


def unknown_annotations_to_kwargs(parameters: List[FunctionArgument]) -> List[FunctionArgument]:
    from giskard.datasets.base import Dataset
    from giskard.models.base import BaseModel
    from giskard.registry.slicing_function import SlicingFunction
    from giskard.registry.transformation_function import TransformationFunction

    allowed_types = [str, bool, int, float, BaseModel, Dataset, SlicingFunction, TransformationFunction]
    allowed_types = list(map(lambda x: x.__qualname__, allowed_types))

    kwargs = [param for param in parameters if not any([param.type == allowed_type for allowed_type in allowed_types])]

    parameters = [param for param in parameters if any([param.type == allowed_type for allowed_type in allowed_types])]

    for idx, parameter in enumerate(parameters):
        parameter.argOrder = idx

    if any(kwargs) > 0:
        kwargs_with_default = [param for param in kwargs if param.default != inspect.Parameter.empty]
        default_value = (
            dict({param.name: param.default for param in kwargs_with_default}) if any(kwargs_with_default) else None
        )

        parameters.append(
            FunctionArgument(
                name="kwargs",
                type="Kwargs",
                default=default_value,
                optional=len(kwargs_with_default) == len(kwargs),
                argOrder=len(parameters),
            )
        )

    return parameters


def extract_optional(field):
    if typing.get_origin(field) is Union and NoneType in typing.get_args(field):
        return Union[tuple([arg for arg in typing.get_args(field) if arg is not None and arg is not NoneType])]
    else:
        return field


class ComparisonType(str, Enum):
    IS = "IS"
    IS_NOT = "IS_NOT"
    CONTAINS = "CONTAINS"
    DOES_NOT_CONTAINS = "DOES_NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    IS_EMPTY = "IS_EMPTY"
    IS_NOT_EMPTY = "IS_NOT_EMPTY"


class TestResultStatusEnum(str, Enum):
    ERROR = "ERROR"
    PASSED = "PASSED"
    FAILED = "FAILED"
