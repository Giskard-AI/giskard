package ai.giskard.ml;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.worker.MLWorkerGrpc;
import ai.giskard.worker.RunTestRequest;
import ai.giskard.worker.TestResultMessage;
import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.StatusRuntimeException;
import org.apache.commons.lang3.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Objects;
import java.util.concurrent.TimeUnit;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient {
    private final Logger logger;

    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;

    public MLWorkerClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        String id = RandomStringUtils.randomAlphanumeric(8);
        logger = LoggerFactory.getLogger("MLWorkerClient [" + id + "]");

        logger.debug("Creating MLWorkerClient");
        blockingStub = MLWorkerGrpc.newBlockingStub(channel);
    }

    public TestResultMessage runTest(TestSuite testSuite, Test test) {
        RunTestRequest.Builder requestBuilder = RunTestRequest.newBuilder()
            .setCode(test.getCode())
            .setModelPath(testSuite.getModel().getLocation());
        if (testSuite.getTrainDataset() != null) {
            requestBuilder.setTrainDatasetPath(testSuite.getTrainDataset().getLocation());
        }
        if (testSuite.getTestDataset() != null) {
            requestBuilder.setTestDatasetPath(testSuite.getTestDataset().getLocation());
        }
        RunTestRequest request = requestBuilder
            .build();
        TestResultMessage testResultMessage = null;
        try {
            testResultMessage = blockingStub.runTest(request);
        } catch (StatusRuntimeException e) {
            interpretTestExecutionError(testSuite, e);
        }
        return testResultMessage;

    }

    public void shutdown() {
        logger.debug("Shutting down MLWorkerClient");
        Channel channel = this.blockingStub.getChannel();
        if (channel instanceof ManagedChannel) {
            try {
                ((ManagedChannel) channel).shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                logger.error("Failed to shutdown worker", e);
            }
        }
    }

    private void interpretTestExecutionError(TestSuite testSuite, StatusRuntimeException e) {
        switch (Objects.requireNonNull(e.getStatus().getDescription())) {
            case "Exception calling application: name 'train_df' is not defined":
                if (testSuite.getTrainDataset() == null) {
                    throw new RuntimeException("Failed to execute test: Train dataset is not specified");
                }
            case "Exception calling application: name 'test_df' is not defined":
                if (testSuite.getTestDataset() == null) {
                    throw new RuntimeException("Failed to execute test: Test dataset is not specified");
                }
            default:
                throw e;
        }
    }
}
