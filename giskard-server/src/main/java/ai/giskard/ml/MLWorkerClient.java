package ai.giskard.ml;

import ai.giskard.domain.ml.testing.Test;
import ai.giskard.worker.*;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.protobuf.ByteString;
import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.stub.AbstractStub;
import lombok.Getter;
import org.apache.commons.lang3.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient implements AutoCloseable {
    private final Logger logger;

    @Getter
    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;
    @Getter
    private final MLWorkerGrpc.MLWorkerFutureStub futureStub;

    public MLWorkerClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        String id = RandomStringUtils.randomAlphanumeric(8); // NOSONAR: no security risk here
        logger = LoggerFactory.getLogger("MLWorkerClient [" + id + "]");

        logger.debug("Creating MLWorkerClient");
        blockingStub = MLWorkerGrpc.newBlockingStub(channel);
        futureStub = MLWorkerGrpc.newFutureStub(channel);
    }

    public ListenableFuture<TestResultMessage> runTest(
        InputStream modelInputStream,
        InputStream trainDFStream,
        InputStream testDFStream,
        Test test
    ) throws IOException {
        RunTestRequest.Builder requestBuilder = RunTestRequest.newBuilder()
            .setCode(test.getCode())
            .setSerializedModel(ByteString.readFrom(modelInputStream));
        if (trainDFStream != null) {
            requestBuilder.setSerializedTrainDf(ByteString.readFrom(trainDFStream));
        }
        if (testDFStream != null) {
            requestBuilder.setSerializedTestDf(ByteString.readFrom(testDFStream));
        }
        RunTestRequest request = requestBuilder.build();
        logger.debug("Sending requiest to ML Worker: {}", request);
        return futureStub.runTest(request);
    }

    public RunModelResponse runModelForDataStream(InputStream modelInputStream, InputStream datasetInputStream, String target) throws IOException {
        RunModelRequest request = RunModelRequest.newBuilder()
            .setSerializedModel(ByteString.readFrom(modelInputStream))
            .setSerializedData(ByteString.readFrom(datasetInputStream))
            .setTarget(target)
            .build();

        return blockingStub.runModel(request);
    }

    public ExplainResponse explain(InputStream modelInputStream, InputStream datasetInputStream, Map<String, String> features) throws IOException {
        ExplainRequest request = ExplainRequest.newBuilder()
            .setSerializedModel(ByteString.readFrom(modelInputStream))
            .setSerializedData(ByteString.readFrom(datasetInputStream))
            .putAllFeatures(features)
            .build();

        return blockingStub.explain(request);
    }

    public RunModelForDataFrameResponse runModelForDataframe(InputStream modelInputStream, DataFrame df) throws IOException {
        RunModelForDataFrameRequest request = RunModelForDataFrameRequest.newBuilder()
            .setSerializedModel(ByteString.readFrom(modelInputStream))
            .setDataframe(df)
            .build();

        return blockingStub.runModelForDataFrame(request);
    }

    public void shutdown() {
        logger.debug("Shutting down MLWorkerClient");
        Stream.of(this.blockingStub, this.futureStub).map(AbstractStub::getChannel).forEach(channel -> {
            if (channel instanceof ManagedChannel managedChannel) {
                try {
                    managedChannel.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
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
