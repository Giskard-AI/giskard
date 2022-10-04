package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import io.grpc.ClientInterceptor;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.unit.DataSize;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;


    public MLWorkerClient createClient() {
        ClientInterceptor clientInterceptor = new MLWorkerClientErrorInterceptor();

        ManagedChannel channel = ManagedChannelBuilder.forAddress(getMlWorkerHost(), getMlWorkerPort())
            .intercept(clientInterceptor)
            .usePlaintext()
            .maxInboundMessageSize((int) DataSize.ofMegabytes(applicationProperties.getMaxInboundMLWorkerMessageMB()).toBytes())
            .build();


        return new MLWorkerClient(channel);
    }

    private int getMlWorkerPort() {
        if (applicationProperties.isExternalMlWorkerEnabled() && mlWorkerTunnelService.getTunnelPort().isPresent()) {
            return mlWorkerTunnelService.getTunnelPort().get();
        }
        return applicationProperties.getMlWorkerPort();
    }

    private String getMlWorkerHost() {
        if (applicationProperties.isExternalMlWorkerEnabled()) {
            return "localhost";
        }
        return applicationProperties.getMlWorkerHost();
    }
}
