package ai.giskard.ml;

import ai.giskard.worker.MLWorkerGrpc;
import io.grpc.Channel;
import io.grpc.ManagedChannel;
import lombok.Getter;
import org.apache.commons.lang3.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.TimeUnit;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient implements AutoCloseable {
    private final Logger logger;

    @Getter
    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;
    @Getter
    private final MLWorkerGrpc.MLWorkerStub nonBlockingStub;
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
        nonBlockingStub = MLWorkerGrpc.newStub(channel);
        futureStub = MLWorkerGrpc.newFutureStub(channel);
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
