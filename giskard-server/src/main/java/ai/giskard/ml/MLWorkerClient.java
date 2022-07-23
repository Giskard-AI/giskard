package ai.giskard.ml;

import ai.giskard.config.SpringContext;
import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.exception.MLWorkerRuntimeException;
import ai.giskard.service.GRPCMapper;
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
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient implements AutoCloseable {
    private final Logger logger;

    @Getter
    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;

    private final GRPCMapper grpcMapper;

    public MLWorkerClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        String id = RandomStringUtils.randomAlphanumeric(8); // NOSONAR: no security risk here
        logger = LoggerFactory.getLogger("MLWorkerClient [" + id + "]");
        this.grpcMapper = SpringContext.getBean(GRPCMapper.class);
        logger.debug("Creating MLWorkerClient");
        blockingStub = MLWorkerGrpc.newBlockingStub(channel);
    }

    public TestResultMessage runTest(
        ProjectModel model,
        ByteString referenceDFStream,
        Dataset referenceDS,
        ByteString actualDFStream,
        Dataset actualDS,
        Test test
    ) throws IOException {
        RunTestRequest.Builder requestBuilder = RunTestRequest.newBuilder()
            .setCode(test.getCode())
            .setModel(grpcMapper.serialize(model));
        if (referenceDFStream != null) {
            requestBuilder.setReferenceDs(grpcMapper.serialize(referenceDS));
        }
        if (actualDFStream != null) {
            requestBuilder.setActualDs(grpcMapper.serialize(actualDS));
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

    public RunModelForDataFrameResponse runModelForDataframe(ProjectModel model, Dataset dataset, Map<String, String> features) throws IOException {
        RunModelForDataFrameRequest.Builder requestBuilder = RunModelForDataFrameRequest.newBuilder()
            .setModel(grpcMapper.serialize(model))
            .setDataframe(DataFrame.newBuilder().addRows(DataRow.newBuilder().putAllColumns(features)).build());
        if(dataset.getTarget() != null){
            requestBuilder.setTarget(dataset.getTarget());
        }
        if(dataset.getFeatureTypes() != null){
            requestBuilder.putAllFeatureTypes(Maps.transformValues(dataset.getFeatureTypes(), FeatureType::getName));
        }
        if(dataset.getColumnTypes() != null){
            requestBuilder.putAllColumnTypes(dataset.getColumnTypes());
        }
        return blockingStub.runModelForDataFrame(requestBuilder.build());
    }

    public RunModelResponse runModelForDataStream(ProjectModel model, Dataset dataset) throws IOException {
        Map<String, String> columnTypes = dataset.getColumnTypes();
        RunModelRequest request = RunModelRequest.newBuilder()
            .setModel(grpcMapper.serialize(model))
            .setDataset(grpcMapper.serialize(dataset))
            .build();

        return blockingStub.runModel(request);
    }

    public ExplainResponse explain(ProjectModel model, Dataset dataset, Map<String, String> sample) throws IOException {
        ExplainRequest request = ExplainRequest.newBuilder()
            .setModel(grpcMapper.serialize(model))
            .setDataset(grpcMapper.serialize(dataset))
            .putAllColumns(sample)
            .build();

        return blockingStub.explain(request);
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
