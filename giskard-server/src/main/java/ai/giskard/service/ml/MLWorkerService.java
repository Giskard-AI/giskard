package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import io.grpc.ClientInterceptor;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.springframework.stereotype.Service;
import org.springframework.util.unit.DataSize;

@Service
public class MLWorkerService {
    private final ApplicationProperties applicationProperties;


    public MLWorkerClient createClient() {
        ClientInterceptor clientInterceptor = new MLWorkerClientErrorInterceptor();

        ManagedChannel channel = ManagedChannelBuilder.forAddress(
                applicationProperties.getMlWorkerHost(),
                applicationProperties.getMlWorkerPort()
            )
            .intercept(clientInterceptor)
            // Channels are secure by default (via SSL/TLS). For the example we disable TLS to avoid
            // needing certificates.
            .usePlaintext()
            .maxInboundMessageSize((int) DataSize.ofMegabytes(applicationProperties.getMaxInboundMLWorkerMessageMB()).toBytes())
            .build();


        return new MLWorkerClient(channel);
    }

    public MLWorkerService(ApplicationProperties applicationProperties) {
        this.applicationProperties = applicationProperties;
    }
}
