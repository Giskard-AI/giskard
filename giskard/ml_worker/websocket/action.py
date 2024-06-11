from typing import Any, Literal

from enum import Enum
from uuid import UUID

import pydantic
from packaging import version

from giskard.core.validation import ConfiguredBaseModel

IS_PYDANTIC_V2 = version.parse(pydantic.version.VERSION) >= version.parse("2.0")


# Make it so we can use enum in pydantic to parse object
class MLWorkerAction(str, Enum):
    getInfo = "getInfo"
    runAdHocTest = "runAdHocTest"
    datasetProcessing = "datasetProcessing"
    runTestSuite = "runTestSuite"
    runModel = "runModel"
    runModelForDataFrame = "runModelForDataFrame"
    explain = "explain"
    explainText = "explainText"
    echo = "echo"
    generateTestSuite = "generateTestSuite"
    stopWorker = "stopWorker"
    getCatalog = "getCatalog"
    generateQueryBasedSlicingFunction = "generateQueryBasedSlicingFunction"
    getPush = "getPush"
    createSubDataset = "createSubDataset"
    abort = "abort"
    getLogs = "getLogs"
    createDataset = "createDataset"
    devJob = "devTask"

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
    id: UUID
    action: MLWorkerAction
    param: Any


class ConfigPayload(ConfiguredBaseModel):
    config: Literal["MAX_STOMP_ML_WORKER_REPLY_SIZE"]
    value: int
