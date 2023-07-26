package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.grpc.MLWorkerClientErrorInterceptor;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.MLWorkerWSBaseDTO;
import ai.giskard.ml.dto.MLWorkerWSEchoMsgDTO;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.service.GiskardRuntimeException;
import com.fasterxml.jackson.core.JsonProcessingException;
import io.grpc.ClientInterceptor;
import io.grpc.ManagedChannel;
import io.grpc.netty.NettyChannelBuilder;
import io.netty.channel.local.LocalChannel;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioSocketChannel;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Nullable;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    public static final String HEARTBEAT_MESSAGE = "hb";
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final ApplicationProperties applicationProperties;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;


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
                .maxInboundMessageSize(Integer.MAX_VALUE)
                .eventLoopGroup(isInternal ? new NioEventLoopGroup() : mlWorkerTunnelService.getInnerServerDetails().get().group())
                .usePlaintext().build();

            return new MLWorkerClient(channel);
        } catch (Exception e) {
            log.warn("Failed to create ML Worker client", e);
            String workerType = isInternal ? "internal" : "external";
            String fix = isInternal ? "giskard server restart worker" : "`giskard worker start -u GISKARD_ADDRESS` in the terminal of the machine that will execute the model. For more details refer to documentation: https://docs.giskard.ai/start/guides/installation/ml-worker";
            throw new GiskardRuntimeException(String.format("Failed to establish a connection with %s ML Worker.%nStart it by running %s", workerType, fix), e);
        }
    }

    public boolean isExternalWorkerConnected() {
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

    @Scheduled(fixedRateString = "${giskard.external-worker-heartbeat-interval-seconds:60}", timeUnit = TimeUnit.SECONDS)
    public void sendHeartbeatToConnectedWorkers() {
        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.EXTERNAL)) {
            log.debug("Executing ML Worker heartbeat");
            MLWorkerWSEchoMsgDTO echoMsg = MLWorkerWSEchoMsgDTO.builder()
                .msg(HEARTBEAT_MESSAGE)
                .build();
            MLWorkerWSBaseDTO result= mlWorkerWSCommService.performAction(
                MLWorkerID.EXTERNAL,
                MLWorkerWSAction.echo,
                echoMsg
            );
            if (result instanceof MLWorkerWSEchoMsgDTO reply) {
                if (!HEARTBEAT_MESSAGE.equals(reply.getMsg())) {
                    log.warn("ML Worker heartbeat returned unexpected result: {}", reply.getMsg());
                }
            } else {
                log.warn("Cannot get ML Worker heartbeat message");
            }
        }
    }
}
