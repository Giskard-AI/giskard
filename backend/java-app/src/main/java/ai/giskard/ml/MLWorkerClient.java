/*
 * Copyright 2015 The gRPC Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package ai.giskard.ml;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.worker.*;
import com.google.protobuf.Any;
import com.google.protobuf.InvalidProtocolBufferException;
import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;
import org.apache.commons.lang3.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.TimeUnit;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient {
    private final String id;
    private final Logger logger;

    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;

    public MLWorkerClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        id = RandomStringUtils.randomAlphanumeric(8);
        logger = LoggerFactory.getLogger("MLWorkerClient [" + id + "]");

        logger.debug("Creating MLWorkerClient");
        blockingStub = MLWorkerGrpc.newBlockingStub(channel);
    }

    public void predict() {
        logger.debug("Calling predict");
        PredictRequest request = null;
        try {
            request = PredictRequest.newBuilder()
                .setModelPath("/demo/path")
                .putFeatures("Hello", Any.parseFrom("Hello".getBytes(StandardCharsets.UTF_8)))
                .build();
        } catch (InvalidProtocolBufferException e) {
            logger.warn("failed to initialize features map");
        }
        PredictResponse response;
        try {
            response = blockingStub.predict(request);
        } catch (StatusRuntimeException e) {
            logger.warn("RPC failed: %s", e.getStatus());
            return;
        }
        Map<String, Float> probabilities = response.getProbabilitiesMap();
        logger.info("Prediction results: " + probabilities);
    }

    public TestResultMessage runTest(TestSuite testSuite, Test test) {
        RunTestRequest.Builder requestBuilder = RunTestRequest.newBuilder()
            .setCode(test.getCode())
            .setModelPath(testSuite.getModel().getLocation());
        if (testSuite.getTrainDataset() != null) {
            requestBuilder.setTrainDatasetPath(testSuite.getTrainDataset().getLocation());
        }
        if (testSuite.getTestDataset() != null) {
            requestBuilder.setTestDatasetPath(testSuite.getTestDataset().getLocation());
        }
        RunTestRequest request = requestBuilder
            .build();
        TestResultMessage testResultMessage = null;
        try {
            testResultMessage = blockingStub.runTest(request);
        } catch (StatusRuntimeException e) {
            interpretTestExecutionError(testSuite, e);
        }
        return testResultMessage;

    }

    private void interpretTestExecutionError(TestSuite testSuite, StatusRuntimeException e) {
        switch (Objects.requireNonNull(e.getStatus().getDescription())) {
            case "Exception calling application: name 'train_df' is not defined":
                if (testSuite.getTrainDataset() == null) {
                    throw new RuntimeException("Failed to execute test: Train dataset is not specified");
                }
            case "Exception calling application: name 'test_df' is not defined":
                if (testSuite.getTestDataset() == null) {
                    throw new RuntimeException("Failed to execute test: Test dataset is not specified");
                }
            default:
                throw e;
        }
    }

    public void loadModel(String name) {
        logger.info("Will try to greet " + name + " ...");
        LoadModelRequest request = LoadModelRequest.newBuilder().setName(name).build();
        LoadModelResponse response;
        try {
            response = blockingStub.loadModel(request);
        } catch (StatusRuntimeException e) {
            logger.warn("RPC failed: %s", e.getStatus());
            return;
        }
        logger.info("Greeting: " + response.getMessage());
    }

    public void shutdown() {
        logger.debug("Shutting down MLWorkerClient");
        Channel channel = this.blockingStub.getChannel();
        if (channel instanceof ManagedChannel) {
            try {
                ((ManagedChannel) channel).shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                logger.error("Failed to shutdown worker", e);
            }
        }
    }

    public static MLWorkerClient createClient() throws InterruptedException {
        String target = "localhost:50051";
        ManagedChannel channel = ManagedChannelBuilder.forTarget(target)
            // Channels are secure by default (via SSL/TLS). For the example we disable TLS to avoid
            // needing certificates.
            .usePlaintext()
            .build();

        return new MLWorkerClient(channel);
    }

    /**
     * Greet server. If provided, the first element of {@code args} is the name to use in the
     * greeting. The second argument is the target server.
     */
    public static void main(String[] args) throws Exception {
        String user = "world";
        // Access a service running on the local machine on port 50051
        String target = "localhost:50051";
        // Allow passing in the user and target strings as command line arguments
        if (args.length > 0) {
            if ("--help".equals(args[0])) {
                System.err.println("Usage: [name [target]]");
                System.err.println("");
                System.err.println("  name    The name you wish to be greeted by. Defaults to " + user);
                System.err.println("  target  The server to connect to. Defaults to " + target);
                System.exit(1);
            }
            user = args[0];
        }
        if (args.length > 1) {
            target = args[1];
        }

        // Create a communication channel to the server, known as a Channel. Channels are thread-safe
        // and reusable. It is common to create channels at the beginning of your application and reuse
        // them until the application shuts down.
        ManagedChannel channel = ManagedChannelBuilder.forTarget(target)
            // Channels are secure by default (via SSL/TLS). For the example we disable TLS to avoid
            // needing certificates.
            .usePlaintext()
            .build();
        try {
            MLWorkerClient client = new MLWorkerClient(channel);
            String finalUser = user;
            Thread a = new Thread(() -> {
                client.predict();
            });
            Thread b = new Thread(() -> {
                client.predict();
            });
            a.start();
            b.start();
            a.join();
            b.join();

        } finally {
            // ManagedChannels use resources like threads and TCP connections. To prevent leaking these
            // resources the channel should be shut down when it will no longer be used. If it may be used
            // again leave it running.
            channel.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
        }
    }
}
