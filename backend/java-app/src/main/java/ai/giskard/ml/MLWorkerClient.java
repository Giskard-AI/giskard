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

import ai.giskard.worker.*;
import com.google.protobuf.Any;
import com.google.protobuf.InvalidProtocolBufferException;
import io.grpc.Channel;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * A java-python bridge for model execution
 */
public class MLWorkerClient {
    private static final Logger logger = Logger.getLogger(MLWorkerClient.class.getName());

    private final MLWorkerGrpc.MLWorkerBlockingStub blockingStub;

    public MLWorkerClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        blockingStub = MLWorkerGrpc.newBlockingStub(channel);
    }

    public void predict() {
        PredictRequest request = null;
        try {
            request = PredictRequest.newBuilder()
                .setModelPath("/demo/path")
                .putFeatures("Hello", Any.parseFrom("Hello".getBytes(StandardCharsets.UTF_8)))
                .build();
        } catch (InvalidProtocolBufferException e) {
            logger.log(Level.WARNING, "failed to initialize features map");
        }
        PredictResponse response;
        try {
            response = blockingStub.predict(request);
        } catch (StatusRuntimeException e) {
            logger.log(Level.WARNING, "RPC failed: {0}", e.getStatus());
            return;
        }
        Map<String, Float> probabilities = response.getProbabilitiesMap();
        logger.info("Prediction results: " + probabilities);

    }

    public void loadModel(String name) {
        logger.info("Will try to greet " + name + " ...");
        LoadModelRequest request = LoadModelRequest.newBuilder().setName(name).build();
        LoadModelResponse response;
        try {
            response = blockingStub.loadModel(request);
        } catch (StatusRuntimeException e) {
            logger.log(Level.WARNING, "RPC failed: {0}", e.getStatus());
            return;
        }
        logger.info("Greeting: " + response.getMessage());
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
