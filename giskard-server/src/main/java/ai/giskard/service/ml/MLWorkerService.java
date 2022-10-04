package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import io.grpc.ClientInterceptor;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.unit.DataSize;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;


    public MLWorkerClient createClient() {
        ClientInterceptor clientInterceptor = new MLWorkerClientErrorInterceptor();
        String host = getMlWorkerHost();
        int port = getMlWorkerPort();
        log.info("Creating MLWorkerClient for {}:{}", host, port);

        ManagedChannel channel = ManagedChannelBuilder.forAddress(host, port)
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
        if (applicationProperties.isExternalMlWorkerEnabled() && mlWorkerTunnelService.getTunnelPort().isPresent()) {
            return "localhost";
        }
        return applicationProperties.getMlWorkerHost();
    }
}
