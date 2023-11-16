from typing import Any, Literal

from enum import Enum

import pydantic
from packaging import version

from giskard.core.validation import ConfiguredBaseModel

IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")


# Make it so we can use enum in pydantic to parse object
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
    getPush = 13
    createSubDataset = 14

    @classmethod
    def __get_validators__(cls):
        if IS_PYDANTIC_V2:
            yield cls.validate
        else:
            yield cls.validate_v1

    @classmethod
    def validate(cls, v, *args, **kwargs):
        return cls.validate_v1(v)

    @classmethod
    def validate_v1(cls, value, values=None, config=None, field=None):
        try:
            return cls[value]
        except KeyError as e:
            raise ValueError(f"Unknown value {value}") from e


class ActionPayload(ConfiguredBaseModel):
    id: str
    action: MLWorkerAction
    param: Any


class ConfigPayload(ConfiguredBaseModel):
    config: Literal["MAX_STOMP_ML_WORKER_REPLY_SIZE"]
    value: int
