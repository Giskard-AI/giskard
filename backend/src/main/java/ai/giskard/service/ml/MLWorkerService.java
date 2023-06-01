package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.FileUploadService;
import ai.giskard.service.GiskardRuntimeException;
import ai.giskard.worker.*;
import com.google.protobuf.ByteString;
import io.grpc.ClientInterceptor;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.unit.DataSize;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    public static final int FILTER_CHUNK_SIZE_ROWS = 5000; // TODO: https://github.com/Giskard-AI/giskard/issues/660
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private final FileLocationService locationService;
    private final FileUploadService fileUploadService;

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
                String fix = isInternal ? "docker-compose up -d ml-worker" : "`giskard worker start -h GISKARD_ADDRESS` in the terminal of the machine that will execute the model. For more details refer to documentation: https://docs.giskard.ai/start/guides/installation/ml-worker";
                throw new GiskardRuntimeException(String.format("Failed to establish a connection with %s ML Worker.%nStart it by running %s", workerType, fix), e);
            }
            return null;
        }
    }

    public List<Integer> filterDataset(MLWorkerClient client, Dataset dataset, String function, Integer limit) throws IOException {
        log.info("Filtering dataset {}", dataset.getName());
        Path path = locationService.resolvedDatasetPath(dataset).resolve("data.csv.zst");

        AtomicReference<StreamObserver<FilterDatasetRequest>> requestObserverRef = new AtomicReference<>();
        List<Integer> validRows = new ArrayList<>();
        CountDownLatch finishedLatch = new CountDownLatch(1);
        try (InputStream inputStream = fileUploadService.decompressFileToStream(path)) { // Maybe decompressFileToStream should go in some utils?
            // Read headers
            BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
            String headers = reader.readLine();
            AtomicReference<String> error = new AtomicReference<>();

            StreamObserver<FilterDatasetRequest> observer = client.getNonBlockingStub().filterDataset(
                new FilterDatasetResponseStreamObserver(requestObserverRef, finishedLatch, reader, validRows, limit, error)
            );
            requestObserverRef.set(observer);

            FilterDatasetMetadata.Builder metaBuilder = FilterDatasetMetadata.newBuilder()
                .setHeaders(headers)
                .setFunction(function);
            if (dataset.getColumnTypes() != null) {
                metaBuilder.putAllColumnTypes(dataset.getColumnTypes());
            }
            FilterDatasetRequest metadata = FilterDatasetRequest.newBuilder()
                .setMeta(metaBuilder.build())
                .setIdx(0)
                .build();

            observer.onNext(metadata);

            try {
                finishedLatch.await();
                if (error.get() != null) {
                    throw new GiskardRuntimeException(error.get());
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                log.warn("Interrupted while filtering a dataset: {}", dataset.getName());
                throw new GiskardRuntimeException("Interrupted while filtering a dataset");
            }
        }

        return validRows;
    }

    @RequiredArgsConstructor
    private class FilterDatasetResponseStreamObserver implements StreamObserver<FilterDatasetResponse> {
        private final AtomicReference<StreamObserver<FilterDatasetRequest>> requestObserverRef;
        private final CountDownLatch finishedLatch;
        private final BufferedReader reader;
        private final List<Integer> result;
        private final Integer limit;
        private final AtomicReference<String> error;

        @SneakyThrows
        @Override
        public void onNext(FilterDatasetResponse value) {
            if (StatusCode.Ready.equals(value.getCode())) {
                log.info("Sending data for slicing.");
                // Start streaming requests. For now, use arbitrary chunk size of FILTER_CHUNK_SIZE_ROWS lines
                int linesRead = 0;
                int idx = 0;
                String line;
                StringBuilder sb = new StringBuilder();
                while ((line = reader.readLine()) != null) { // Will read every line...
                    linesRead++;
                    sb.append(line).append("\n");

                    // If our limit is set, and we hit it, we stop reading the file.
                    if (limit > 0 && linesRead > limit) {
                        break;
                    }

                    if (linesRead == FILTER_CHUNK_SIZE_ROWS) {
                        requestObserverRef.get().onNext(
                            FilterDatasetRequest.newBuilder()
                                .setData(Chunk.newBuilder().setContent(ByteString.copyFrom(sb.toString(), StandardCharsets.UTF_8)).build())
                                .setIdx(idx)
                                .build()
                        );
                        linesRead = 0;
                        sb = new StringBuilder();
                        idx++;
                    }
                }

                if (linesRead > 0) { // We still had some in the buffer, send em
                    requestObserverRef.get().onNext(
                        FilterDatasetRequest.newBuilder()
                            .setData(Chunk.newBuilder().setContent(ByteString.copyFrom(sb.toString(), "utf-8")).build())
                            .setIdx(idx)
                            .build()
                    );
                }

                requestObserverRef.get().onCompleted();
            } else if (StatusCode.Next.equals(value.getCode())) {
                result.addAll(value.getRowsList()
                    .stream()
                    .map(x -> x + (value.getIdx() * FILTER_CHUNK_SIZE_ROWS)) // We add because the outgoing row IDs are 0 based...
                    .toList());
            } else if (StatusCode.Ok.equals(value.getCode())) {
                // Consider complete, close reader/writer.
                log.info("Slicing done, {} results returned.", result.size());
            } else if (StatusCode.Failed.equals(value.getCode())) {
                error.set(value.getErrorMessage());
                requestObserverRef.get().onError(new GiskardRuntimeException(value.getErrorMessage()));
            }
        }

        @Override
        public void onError(Throwable t) {
            finishedLatch.countDown();
        }

        @Override
        public void onCompleted() {
            finishedLatch.countDown();
        }
    }

    private int getMlWorkerPort(boolean isInternal) {
        if (isInternal || !applicationProperties.isExternalMlWorkerEnabled()) {
            return applicationProperties.getMlWorkerPort();
        } else {
            return mlWorkerTunnelService.getTunnelPort()
                .orElseThrow(() -> new GiskardRuntimeException("No external worker is connected"));
        }
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
