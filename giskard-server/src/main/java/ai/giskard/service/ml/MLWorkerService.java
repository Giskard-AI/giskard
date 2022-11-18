package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ProjectFile;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.GiskardRuntimeException;
import ai.giskard.worker.*;
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
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    public static final int UPLOAD_FILE_CHUNK_KB = 256;
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private final FileLocationService locationService;

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
                String fix = isInternal ? "docker-compose up -d ml-worker" : "giskard worker start -h GISKARD_ADDRESS";
                throw new GiskardRuntimeException(String.format("Failed to establish a connection with %s ML Worker. Start it with \"%s\"", workerType, fix), e);
            }
            return null;
        }
    }

    // synchronizing in order not to corrupt a file on an ML worker file in case of concurrent
    // model execution
    public synchronized UploadStatus upload(MLWorkerClient client, ProjectFile file) throws IOException {
        log.info("Uploading {}", file.getFileName());
        Path path = locationService.resolveFilePath(file);

        AtomicReference<StreamObserver<FileUploadRequest>> requestObserverRef = new AtomicReference<>();
        AtomicReference<UploadStatus> result = new AtomicReference<>();
        CountDownLatch finishedLatch = new CountDownLatch(1);
        try (InputStream inputStream = Files.newInputStream(path)) {
            StreamObserver<FileUploadRequest> observer = client.getNonBlockingStub().upload(
                new UploadStatusStreamObserver(file, inputStream, requestObserverRef, result, finishedLatch)
            );
            requestObserverRef.set(observer);

            FileType fileType = determineFileTYpe(file);

            FileUploadRequest metadata = FileUploadRequest.newBuilder()
                .setMetadata(
                    FileUploadMetadata.newBuilder()
                        .setId(file.getId())
                        .setFileType(fileType)
                        .setName(file.getFileName())
                        .setProjectKey(file.getProject().getKey())
                        .build())
                .build();

            observer.onNext(metadata);

            try {
                finishedLatch.await();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                log.warn("Interrupted while uploading a file: {}", file.getFileName());
                throw new GiskardRuntimeException("Interrupted while uploading a file");
            }
        }
        return result.get();
    }

    private static FileType determineFileTYpe(ProjectFile file) {
        FileType fileType;
        if (file instanceof ProjectModel) {
            fileType = FileType.MODEL;
        } else if (file instanceof Dataset) {
            fileType = FileType.DATASET;
        } else {
            throw new IllegalArgumentException(String.format("Upload object should be either model or dataset, got %s", file.getClass().getCanonicalName()));
        }
        return fileType;
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

    @RequiredArgsConstructor
    private class UploadStatusStreamObserver implements StreamObserver<UploadStatus> {
        private final ProjectFile file;
        private final InputStream inputStream;
        private final AtomicReference<StreamObserver<FileUploadRequest>> requestObserverRef;
        private final AtomicReference<UploadStatus> result;
        private final CountDownLatch finishedLatch;

        @Override
        public void onNext(UploadStatus uploadStatus) {
            if (UploadStatusCode.CacheMiss.equals(uploadStatus.getCode())) {
                log.info("Transferring file {}", file.getFileName());
                try {
                    streamFile(inputStream, requestObserverRef.get());
                } catch (IOException e) {
                    throw new GiskardRuntimeException("Error while uploading file", e);
                }
            } else {
                log.info("File uploaded {}", file.getFileName());
                result.set(uploadStatus);
            }
            requestObserverRef.get().onCompleted();
        }

        @Override
        public void onCompleted() {
            finishedLatch.countDown();
        }

        @Override
        public void onError(Throwable throwable) {
            finishedLatch.countDown();
        }
    }
}
