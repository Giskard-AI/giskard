package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.ml.MLWorkerClient;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.springframework.stereotype.Service;

@Service
public class MLWorkerService {
    private final ApplicationProperties applicationProperties;

    public MLWorkerClient createClient() {
        ManagedChannel channel = ManagedChannelBuilder.forAddress(
                applicationProperties.getMlWorkerHost(),
                applicationProperties.getMlWorkerPort()
            )
            // Channels are secure by default (via SSL/TLS). For the example we disable TLS to avoid
            // needing certificates.
            .usePlaintext().build();

        return new MLWorkerClient(channel);
    }

    public MLWorkerService(ApplicationProperties applicationProperties) {
        this.applicationProperties = applicationProperties;
    }
}
