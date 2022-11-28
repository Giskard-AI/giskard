package ai.giskard.ml;

import ai.giskard.worker.EchoMsg;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.List;
import java.util.stream.IntStream;

@Disabled
class MLWorkerClientTest {
    public MLWorkerClient createClient() {
        int proxyPort = 50051;
        //int realPort = 50051;
        ManagedChannel channel = ManagedChannelBuilder.forAddress("localhost", proxyPort)
            .usePlaintext()
            .build();
        return new MLWorkerClient(channel);
    }


    @Test
    void testClientSimple() {
        runTest();
    }

    @Test
    void testClient() throws InterruptedException {
        List<Thread> threads = IntStream.range(0, 5)
            .mapToObj(operand -> new Thread(this::runTest, "thread_" + operand))
            .toList();
        threads.forEach(Thread::start);

        for (Thread thread : threads) {
            thread.join();
        }

    }

    private void runTest() {
        Instant start = Instant.now();
        int runs = 5;
        for (int t = 0; t < 500; t++) {
            try (MLWorkerClient client = createClient()) {
                for (int i = 0; i < runs; i++) {
                    EchoMsg response = client.getBlockingStub().echo(EchoMsg.newBuilder().setMsg("Hello " + i).build());
                    System.out.printf("%s: Try %d : %s%n", Thread.currentThread().getName(), t, response.getMsg());
                }
            }
        }
        long elapsed = Instant.now().toEpochMilli() - start.toEpochMilli();
        System.out.printf("All: %s, one %s%n", elapsed, elapsed / runs);
    }
}
