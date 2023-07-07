package ai.giskard.ml;

public enum MLWorkerWSAction {
    getInfo,
    runAdHocTest,
    datasetProcessing,
    runTestSuite,
    runModel,
    runModelForDataFrame,
    explain,
    explainText,
    echo,
    generateTestSuite,
    stopWorker,
    getCatalog,
    generateQueryBasedSlicingFunction,
}
