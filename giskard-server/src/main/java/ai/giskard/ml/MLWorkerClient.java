package ai.giskard.ml;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.exception.MLWorkerRuntimeException;
import ai.giskard.worker.*;
import com.google.common.collect.Maps;
import com.google.protobuf.ByteString;
import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.StatusRuntimeException;
import lombok.Getter;
import org.apache.commons.lang3.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient implements AutoCloseable {
    private final Logger logger;

    @Getter
    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;

    public MLWorkerClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        String id = RandomStringUtils.randomAlphanumeric(8); // NOSONAR: no security risk here
        logger = LoggerFactory.getLogger("MLWorkerClient [" + id + "]");

        logger.debug("Creating MLWorkerClient");
        blockingStub = MLWorkerGrpc.newBlockingStub(channel);
    }

    public TestResultMessage runTest(
        ByteString modelInputStream,
        ByteString referenceDFStream,
        Dataset referenceDS,
        ByteString actualDFStream,
        Dataset actualDS,
        Test test
    ) {
        RunTestRequest.Builder requestBuilder = RunTestRequest.newBuilder()
            .setCode(test.getCode())
            .setSerializedModel(modelInputStream);
        if (referenceDFStream != null) {
            requestBuilder.setReferenceDs(
                SerializedGiskardDataset.newBuilder()
                    .setSerializedDf(referenceDFStream)
                    .setTarget(referenceDS.getTarget())
                    .putAllFeatureTypes(Maps.transformValues(referenceDS.getFeatureTypes(), FeatureType::getName))
                    .build());
        }
        if (actualDFStream != null) {
            requestBuilder.setActualDs(
                SerializedGiskardDataset.newBuilder()
                    .setSerializedDf(actualDFStream)
                    .setTarget(actualDS.getTarget())
                    .putAllFeatureTypes(Maps.transformValues(actualDS.getFeatureTypes(), FeatureType::getName))
                    .build());
        }
        RunTestRequest request = requestBuilder.build();
        logger.debug("Sending requiest to ML Worker: {}", request);
        try {
            return blockingStub.runTest(request);
        } catch (StatusRuntimeException e) {
            if (e.getCause() instanceof MLWorkerRuntimeException mlWorkerRE) {
                mlWorkerRE.setMessage(String.format("Failed to execute test: %s", test.getName()));
                throw mlWorkerRE;
            }
            throw e;
        }
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
        if (this.blockingStub.getChannel() instanceof ManagedChannel managedChannel) {
            try {
                managedChannel.shutdownNow().awaitTermination(15, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                logger.error("Failed to shutdown worker", e);
            }
        }
    }

    @Override
    public void close() {
        this.shutdown();
    }
}
