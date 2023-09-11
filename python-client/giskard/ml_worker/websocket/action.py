from enum import Enum


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
