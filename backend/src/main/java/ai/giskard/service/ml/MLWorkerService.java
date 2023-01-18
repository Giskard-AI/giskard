package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.service.GiskardRuntimeException;
import io.grpc.ClientInterceptor;
import io.grpc.ManagedChannel;
import io.grpc.netty.NettyChannelBuilder;
import io.netty.channel.local.LocalChannel;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioSocketChannel;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.annotation.Nullable;
import java.net.InetSocketAddress;
import java.net.SocketAddress;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;


    @Nullable
    public MLWorkerClient createClientNoError(boolean isInternal) {
        try {
            return createClient(isInternal);
        } catch (Exception e) {
            log.error("Failed to create ML Worker client", e);
            return null;
        }
    }

    public MLWorkerClient createClient(boolean isInternal) {
        try {
            ClientInterceptor clientInterceptor = new MLWorkerClientErrorInterceptor();
            SocketAddress address = getMLWorkerAddress(isInternal);
            log.info("Creating MLWorkerClient for {}", address.toString());

            ManagedChannel channel = NettyChannelBuilder.forAddress(address)
                .intercept(clientInterceptor)
                .channelType(isInternal ? NioSocketChannel.class : LocalChannel.class)
                .eventLoopGroup(isInternal ? new NioEventLoopGroup() : mlWorkerTunnelService.getInnerServerDetails().get().group())
                .usePlaintext()
                .build();

            return new MLWorkerClient(channel);
        } catch (Exception e) {
            log.warn("Failed to create ML Worker client", e);
            String workerType = isInternal ? "internal" : "external";
            String fix = isInternal ? "docker-compose up -d ml-worker" : "giskard worker start -h GISKARD_ADDRESS in the environment that can execute the specified model";
            throw new GiskardRuntimeException(String.format("Failed to establish a connection with %s ML Worker. Start it with \"%s\"", workerType, fix), e);
        }
    }

    private SocketAddress getMLWorkerAddress(boolean isInternal) {
        if (!isInternal && mlWorkerTunnelService.getInnerServerDetails().isEmpty()) {
            throw new GiskardRuntimeException("No external worker is connected");
        }
        if (isInternal || !applicationProperties.isExternalMlWorkerEnabled()) {
            return new InetSocketAddress(applicationProperties.getMlWorkerHost(), applicationProperties.getMlWorkerPort());
        }
        return mlWorkerTunnelService.getInnerServerDetails().get().localAddress();
    }
}
