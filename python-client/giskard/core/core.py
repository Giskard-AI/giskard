from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, TypeVar


class SupportedModelTypes(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class SupportedFeatureTypes(Enum):
    NUMERIC = "numeric"
    CATEGORY = "category"
    TEXT = "text"


class SavableMeta:
    uuid: Optional[str]

    def __init__(self, uuid: Optional[str]):
        self.uuid = uuid

    def to_json(self):
        return {
            "uuid": self.uuid
        }

    @classmethod
    def from_json(cls, json):
        return cls(uuid=json["uuid"])


@dataclass
class ModelMeta:
    name: Optional[str]
    model_type: SupportedModelTypes
    feature_names: List[str]
    classification_labels: List[str]
    classification_threshold: float


@dataclass
class DatasetMeta:
    name: Optional[str]
    target: str
    feature_types: Dict[str, str]
    column_types: Dict[str, str]


@dataclass
class TestFunctionArgument:
    name: str
    type: str
    default: any
    optional: bool


class TestFunctionMeta(SavableMeta):
    code: str
    name: str
    display_name: str
    module: str
    doc: str
    module_doc: str
    args: Dict[str, TestFunctionArgument]
    tags: List[str]
    version: Optional[int]

    def __init__(self,
                 uuid: str,
                 code: str,
                 name: str,
                 display_name: str,
                 module: str,
                 doc: str,
                 module_doc: str,
                 args: Dict[str, TestFunctionArgument],
                 tags: List[str],
                 version: Optional[int]):
        super(TestFunctionMeta, self).__init__(uuid)
        self.code = code
        self.name = name
        self.display_name = display_name
        self.module = module
        self.doc = doc
        self.module_doc = module_doc
        self.args = args
        self.tags = tags
        self.version = version

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
            "args":
                [
                    {
                        "name": arg.name,
                        "type": arg.type,
                        "default": arg.default,
                        "optional": arg.optional
                    } for arg in self.args.values()
                ]
        }

    @classmethod
    def from_json(cls, json):
        cls(
            uuid=json["uuid"],
            name=json["name"],
            display_name=json["displayName"],
            module=json["module"],
            doc=json["doc"],
            module_doc=json["moduleDoc"],
            code=json["code"],
            tags=json["tags"],
            version=json["version"],
            args=
            {
                arg["name"]: TestFunctionArgument(
                    name=arg["name"],
                    type=arg["type"],
                    default=arg["defaultValue"],
                    optional=arg["optional"]
                ) for arg in json["args"]
            }
        )


DT = TypeVar('DT')
SMT = TypeVar('SMT', bound=SavableMeta)
