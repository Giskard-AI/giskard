package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.service.GiskardRuntimeException;
import ai.giskard.worker.Chunk;
import ai.giskard.worker.FileUploadRequest;
import com.google.protobuf.ByteString;
import io.grpc.ClientInterceptor;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.unit.DataSize;

import java.io.IOException;
import java.io.InputStream;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    public static final int UPLOAD_FILE_CHUNK_KB = 256;
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;

    private static void streamFile(InputStream inputStream, StreamObserver<FileUploadRequest> streamObserver) throws IOException {
        byte[] bytes = new byte[1024 * UPLOAD_FILE_CHUNK_KB];
        int size;
        while ((size = inputStream.read(bytes)) > 0) {
            streamObserver.onNext(
                FileUploadRequest.newBuilder()
                    .setChunk(Chunk.newBuilder().setContent(ByteString.copyFrom(bytes, 0, size)).build())
                    .build()
            );
        }
    }

    public MLWorkerClient createClient(boolean isInternal) {
        return createClient(isInternal, true);
    }

    public MLWorkerClient createClient(boolean isInternal, boolean raiseExceptionOnFailure) {
        try {
            ClientInterceptor clientInterceptor = new MLWorkerClientErrorInterceptor();
            String host = getMlWorkerHost(isInternal);
            int port = getMlWorkerPort(isInternal);
            log.info("Creating MLWorkerClient for {}:{}", host, port);

            ManagedChannel channel = ManagedChannelBuilder.forAddress(host, port)
                .intercept(clientInterceptor)
                .usePlaintext()
                .maxInboundMessageSize((int) DataSize.ofMegabytes(applicationProperties.getMaxInboundMLWorkerMessageMB()).toBytes())
                .build();


            return new MLWorkerClient(channel);
        } catch (Exception e) {
            log.warn("Failed to create ML Worker client", e);
            if (raiseExceptionOnFailure) {
                String workerType = isInternal ? "internal" : "external";
                String fix = isInternal ? "docker-compose up -d ml-worker" : "giskard worker start -h GISKARD_ADDRESS in the environment that can execute the specified model";
                throw new GiskardRuntimeException(String.format("Failed to establish a connection with %s ML Worker. Start it with \"%s\"", workerType, fix), e);
            }
            return null;
        }
    }

    private int getMlWorkerPort(boolean isInternal) {
        if (!isInternal && mlWorkerTunnelService.getTunnelPort().isEmpty()) {
            throw new GiskardRuntimeException("No external worker is connected");
        }
        if (isInternal || !applicationProperties.isExternalMlWorkerEnabled()) {
            return applicationProperties.getMlWorkerPort();
        }
        return mlWorkerTunnelService.getTunnelPort().get();
    }

    private String getMlWorkerHost(boolean isInternal) {
        if (!isInternal && mlWorkerTunnelService.getTunnelPort().isEmpty()) {
            throw new GiskardRuntimeException("No external worker is connected");
        }
        if (isInternal || !applicationProperties.isExternalMlWorkerEnabled()) {
            return applicationProperties.getMlWorkerHost();
        }
        return "localhost";
    }

}
