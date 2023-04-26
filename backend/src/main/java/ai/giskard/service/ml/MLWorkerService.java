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
import io.grpc.netty.NettyChannelBuilder;
import io.grpc.stub.StreamObserver;
import io.netty.channel.local.LocalChannel;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioSocketChannel;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;
import org.apache.commons.csv.CSVRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Nullable;
import java.io.*;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    public static final int FILTER_CHUNK_SIZE_ROWS = 5000; // TODO: https://github.com/Giskard-AI/giskard/issues/660
    public static final String HEARTBEAT_MESSAGE = "hb";
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private final FileLocationService locationService;
    private final FileUploadService fileUploadService;


    @Nullable
    public MLWorkerClient createClientNoError(boolean isInternal) {
        try {
            return createClient(isInternal);
        } catch (Exception e) {
            log.error("Failed to create ML Worker client", e);
            return null;
        }
    }

    /**
     * ML Worker operations are time-consuming, we shouldn't perform them inside DB transactions
     */
    @Transactional(propagation = Propagation.NEVER)
    public MLWorkerClient createClient(boolean isInternal) {
        try {
            ClientInterceptor clientInterceptor = new MLWorkerClientErrorInterceptor();
            SocketAddress address = getMLWorkerAddress(isInternal);
            log.info("Creating MLWorkerClient for {}", address);

            ManagedChannel channel = NettyChannelBuilder.forAddress(address).intercept(clientInterceptor).channelType(isInternal ? NioSocketChannel.class : LocalChannel.class)
                .eventLoopGroup(isInternal ? new NioEventLoopGroup() : mlWorkerTunnelService.getInnerServerDetails().get().group())
                .usePlaintext().build();

            return new MLWorkerClient(channel);
        } catch (Exception e) {
            log.warn("Failed to create ML Worker client", e);
            String workerType = isInternal ? "internal" : "external";
            String fix = isInternal ? "docker-compose up -d ml-worker" : "`giskard worker start -h GISKARD_ADDRESS` in the terminal of the machine that will execute the model. For more details refer to documentation: https://docs.giskard.ai/start/guides/installation/ml-worker";
            throw new GiskardRuntimeException(String.format("Failed to establish a connection with %s ML Worker.%nStart it by running %s", workerType, fix), e);
        }
    }

    public List<Integer> filterDataset(MLWorkerClient client, Dataset dataset, String function, Integer limit) throws IOException {
        log.info("Filtering dataset {}", dataset.getName());
        Path path = locationService.resolvedDatasetPath(dataset).resolve("data.csv.zst");

        AtomicReference<StreamObserver<FilterDatasetRequest>> requestObserverRef = new AtomicReference<>();
        List<Integer> validRows = new ArrayList<>();
        CountDownLatch finishedLatch = new CountDownLatch(1);
        try (InputStream inputStream = fileUploadService.decompressFileToStream(path)) { // Maybe decompressFileToStream should go in some utils?
            // Create record iterator
            BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
            final CSVFormat csvFormat = CSVFormat.Builder.create()
                //.setHeader(HEADERS)
                .setAllowMissingColumnNames(true)
                .build();
            final Iterator<CSVRecord> records = csvFormat.parse(reader).iterator();

            StringWriter sw = new StringWriter();
            CSVPrinter printer = new CSVPrinter(sw, CSVFormat.DEFAULT);
            printer.printRecord(records.next());
            String headers = sw.toString();

            AtomicReference<String> error = new AtomicReference<>();

            StreamObserver<FilterDatasetRequest> observer = client.getNonBlockingStub().filterDataset(new FilterDatasetResponseStreamObserver(requestObserverRef, finishedLatch, records, validRows, limit, error));
            requestObserverRef.set(observer);

            FilterDatasetMetadata.Builder metaBuilder = FilterDatasetMetadata.newBuilder()
                .setHeaders(headers)
                .setFunction(function);
            if (dataset.getColumnDtypes() != null) {
                metaBuilder.putAllColumnDtypes(dataset.getColumnDtypes());
            }
            FilterDatasetRequest metadata = FilterDatasetRequest.newBuilder()
                .setMeta(metaBuilder.build()).setIdx(0).build();

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

    private boolean isExternalWorkerConnected() {
        return mlWorkerTunnelService.getInnerServerDetails().isPresent();
    }

    private SocketAddress getMLWorkerAddress(boolean isInternal) {
        if (!isInternal && !isExternalWorkerConnected()) {
            throw new GiskardRuntimeException("No external worker is connected");
        }
        if (isInternal || !applicationProperties.isExternalMlWorkerEnabled()) {
            return new InetSocketAddress(applicationProperties.getMlWorkerHost(), applicationProperties.getMlWorkerPort());
        }
        return mlWorkerTunnelService.getInnerServerDetails().get().localAddress();
    }

    @RequiredArgsConstructor
    private class FilterDatasetResponseStreamObserver implements StreamObserver<FilterDatasetResponse> {
        private final AtomicReference<StreamObserver<FilterDatasetRequest>> requestObserverRef;
        private final CountDownLatch finishedLatch;
        private final Iterator<CSVRecord> iterator;
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
                StringWriter sw = new StringWriter();
                CSVPrinter printer = new CSVPrinter(sw, CSVFormat.DEFAULT);

                while (iterator.hasNext()) { // Will read every line...
                    CSVRecord line = iterator.next();
                    linesRead++;
                    printer.printRecord(line);
                    printer.println();

                    // If our limit is set, and we hit it, we stop reading the file.
                    if (limit > 0 && linesRead > limit) {
                        break;
                    }

                    if (linesRead == FILTER_CHUNK_SIZE_ROWS) {
                        requestObserverRef.get().onNext(FilterDatasetRequest.newBuilder().setData(Chunk.newBuilder().setContent(ByteString.copyFrom(sw.toString(), StandardCharsets.UTF_8)).build()).setIdx(idx).build());
                        linesRead = 0;
                        idx++;
                        sw.flush();
                    }
                }

                if (linesRead > 0) { // We still had some in the buffer, send em
                    requestObserverRef.get().onNext(FilterDatasetRequest.newBuilder().setData(Chunk.newBuilder().setContent(ByteString.copyFrom(sw.toString(), "utf-8")).build()).setIdx(idx).build());
                }

                requestObserverRef.get().onCompleted();
            } else if (StatusCode.Next.equals(value.getCode())) {
                result.addAll(value.getRowsList().stream().map(x -> x + (value.getIdx() * FILTER_CHUNK_SIZE_ROWS)) // We add because the outgoing row IDs are 0 based...
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

    @Scheduled(fixedRateString = "${giskard.external-worker-heartbeat-interval-seconds:60}", timeUnit = TimeUnit.SECONDS)
    public void sendHeartbeatToConnectedWorkers() {
        if (isExternalWorkerConnected()) {
            log.debug("Executing ML Worker heartbeat");
            try (MLWorkerClient client = createClient(false)) {
                EchoMsg echo = client.getBlockingStub().echo(EchoMsg.newBuilder().setMsg(HEARTBEAT_MESSAGE).build());
                if (!HEARTBEAT_MESSAGE.equals(echo.getMsg())) {
                    log.warn("ML Worker heartbeat returned unexpected result: {}", echo.getMsg());
                }
            } catch (Exception e) {
                log.warn("Failed to perform ML Worker heartbeat", e);
            }
        }
    }
}
