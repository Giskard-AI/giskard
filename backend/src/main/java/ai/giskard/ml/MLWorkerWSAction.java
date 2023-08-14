package ai.giskard.ml;

public enum MLWorkerWSAction {
    GET_INFO("getInfo"),
    RUN_AD_HOC_TEST("runAdHocTest"),
    DATASET_PROCESSING("datasetProcessing"),
    RUN_TEST_SUITE("runTestSuite"),
    RUN_MODEL("runModel"),
    RUN_MODEL_FOR_DATA_FRAME("runModelForDataFrame"),
    EXPLAIN("explain"),
    EXPLAIN_TEXT("explainText"),
    ECHO("echo"),
    GENERATE_TEST_SUITE("generateTestSuite"),
    STOP_WORKER("stopWorker"),
    GET_CATALOG("getCatalog"),
    GENERATE_QUERY_BASED_SLICING_FUNCTION("generateQueryBasedSlicingFunction");

    private final String actionName;
    MLWorkerWSAction(String name) {
        actionName = name;
    }

    @Override
    public String toString() {
        return actionName;
    }
}
