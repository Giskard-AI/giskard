import inspect
import uuid
from enum import Enum
from typing import Any, Optional, Union, Dict

try:
    from types import NoneType
except ImportError:
    # types.NoneType is only available from python >=3.10
    NoneType = type(None)

PRIMITIVES = Union[bool, str, int, float, NoneType]


def _serialize_artifact(artifact, artifact_uuid: Optional[Union[str, uuid.UUID]]) -> str:
    if artifact_uuid is None:
        raise ValueError(f"Cannot serialize artifacts without UUID: {artifact}")

    return str(artifact_uuid)


def repr_parameter(value: Any) -> str:
    if isinstance(value, Enum):
        return repr(value.value)

    return repr(value)


def serialize_parameter(default_value: Any) -> PRIMITIVES:
    if default_value == inspect.Parameter.empty:
        return None

    if isinstance(default_value, PRIMITIVES.__args__):
        return default_value

    if isinstance(default_value, Dict):
        return "\n".join(f"kwargs[{repr(key)}] = {repr_parameter(value)}" for key, value in default_value.items())

    from ..ml_worker.core.savable import Artifact

    if isinstance(default_value, Artifact):
        return _serialize_artifact(default_value, getattr(default_value.meta, "uuid"))

    from giskard.datasets.base import Dataset
    from giskard.models.base import BaseModel

    if isinstance(default_value, Union[BaseModel, Dataset].__args__):
        return _serialize_artifact(default_value, default_value.id)

    raise ValueError(f"Serialization of {type(default_value)} is not supported")
