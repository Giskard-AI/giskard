package ai.giskard.ml;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.service.FileLocationService;
import ai.giskard.worker.*;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.protobuf.ByteString;
import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.stub.AbstractStub;
import org.apache.commons.lang3.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient implements AutoCloseable {
    private final Logger logger;

    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;
    private final MLWorkerGrpc.MLWorkerFutureStub futureStub;

    public MLWorkerClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        String id = RandomStringUtils.randomAlphanumeric(8);
        logger = LoggerFactory.getLogger("MLWorkerClient [" + id + "]");

        logger.debug("Creating MLWorkerClient");
        blockingStub = MLWorkerGrpc.newBlockingStub(channel);
        futureStub = MLWorkerGrpc.newFutureStub(channel);
    }

    public ListenableFuture<TestResultMessage> runTest(TestSuite testSuite, Test test) {
        ProjectModel model = testSuite.getModel();
        RunTestRequest.Builder requestBuilder = RunTestRequest.newBuilder()
            .setCode(test.getCode())
            .setModelPath(FileLocationService.modelRelativePath(model).toString());
        Dataset trainDS = testSuite.getTrainDataset();
        if (trainDS != null) {
            requestBuilder.setTrainDatasetPath(FileLocationService.datasetRelativePath(trainDS).toString());
        }
        Dataset testDS = testSuite.getTestDataset();
        if (testDS != null) {
            requestBuilder.setTestDatasetPath(FileLocationService.datasetRelativePath(testDS).toString());
        }
        RunTestRequest request = requestBuilder.build();
        logger.debug("Sending requiest to ML Worker: {}", request);
        ListenableFuture<TestResultMessage> testResultMessage = null;
        testResultMessage = futureStub.runTest(request);
        return testResultMessage;
    }

    public RunModelResponse runModelForDataStream(InputStream modelInputStream, InputStream datasetInputStream, String target) throws IOException {
        RunModelRequest request = RunModelRequest.newBuilder()
            .setSerializedModel(ByteString.readFrom(modelInputStream))
            .setSerializedData(ByteString.readFrom(datasetInputStream))
            .setTarget(target)
            .build();

        return blockingStub.runModel(request);
    }

    public RunModelForDataFrameResponse runModelForDataframe(InputStream modelInputStream, DataFrame df) throws IOException {
        RunModelRequest request = RunModelRequest.newBuilder()
            .setSerializedModel(ByteString.readFrom(modelInputStream))
            .setData(df)
            .build();

        return blockingStub.runModelForDataFrame(request);
    }

    public void shutdown() {
        logger.debug("Shutting down MLWorkerClient");
        Stream.of(this.blockingStub, this.futureStub).map(AbstractStub::getChannel).forEach(channel -> {
            if (channel instanceof ManagedChannel) {
                try {
                    ((ManagedChannel) channel).shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
                } catch (InterruptedException e) {
                    logger.error("Failed to shutdown worker", e);
                }
            }
        });
    }

    @Override
    public void close() {
        this.shutdown();
    }
}
