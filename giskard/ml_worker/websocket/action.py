from typing import Any, Literal

from enum import Enum

from giskard.core.validation import ConfiguredBaseModel


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

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args, **kwargs):
        try:
            return cls[v]
        except KeyError as e:
            raise ValueError("Unknown value {v}") from e


class ActionPayload(ConfiguredBaseModel):
    id: str
    action: MLWorkerAction
    param: Any


class ConfigPayload(ConfiguredBaseModel):
    config: Literal["MAX_STOMP_ML_WORKER_REPLY_SIZE"]
    value: int
