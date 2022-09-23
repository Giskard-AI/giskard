package ai.giskard.ml;

import ai.giskard.worker.Chunk;
import ai.giskard.worker.EchoMsg;
import ai.giskard.worker.FileUploadMetadata;
import ai.giskard.worker.FileUploadRequest;
import com.google.protobuf.ByteString;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.stub.StreamObserver;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;

class MLWorkerClientTest {
    public MLWorkerClient createClient() {
        int proxyPort = 31524;
        //int realPort = 50051;
        ManagedChannel channel = ManagedChannelBuilder.forAddress("localhost", proxyPort)
            .usePlaintext()
            .build();
        return new MLWorkerClient(channel);
    }

    @Test
    void testClient() {
        Instant start = Instant.now();
        int runs = 30;
        for (int t = 0; t < 100; t++) {
            try (MLWorkerClient client = createClient()) {
                for (int i = 0; i < runs; i++) {
                    EchoMsg response = client.blockingStub.echo(EchoMsg.newBuilder().setMsg("Hello " + i).build());
                    System.out.println("Try %d : %s".formatted(t, response.getMsg()));
                }
            }
        }
        long elapsed = Instant.now().toEpochMilli() - start.toEpochMilli();
        System.out.printf("All: %s, one %s%n", elapsed, elapsed / runs);
    }

    @Test
    void testClientUpload() throws IOException, InterruptedException {
        Instant start = Instant.now();
        try (MLWorkerClient client = createClient()) {
            StreamObserver<FileUploadRequest> streamObserver = client.stub.upload(new FileUploadObserver());


            Path path = Paths.get("/tmp/test.img");
            FileUploadRequest metadata = FileUploadRequest.newBuilder()
                .setMetadata(FileUploadMetadata.newBuilder().setName("testName").build())
                .build();
            streamObserver.onNext(metadata);

            InputStream inputStream = Files.newInputStream(path);
            byte[] bytes = new byte[1024 * 256];
            int size;
            while ((size = inputStream.read(bytes)) > 0) {
                streamObserver.onNext(
                    FileUploadRequest.newBuilder()
                        .setChunk(Chunk.newBuilder().setContent(ByteString.copyFrom(bytes, 0, size)).build())
                        .build()
                );
            }

            inputStream.close();
            streamObserver.onCompleted();
            Thread.sleep(20000);

        }
        long elapsed = Instant.now().toEpochMilli() - start.toEpochMilli();
        System.out.printf("All: %s", elapsed);
    }
}
