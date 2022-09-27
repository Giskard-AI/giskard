package ai.giskard.ml.tunnel;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.ml.tunnel.OuterChannelInitializer.InnerServerStartResponse;
import com.google.common.eventbus.Subscribe;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.net.InetSocketAddress;
import java.util.EventListener;
import java.util.Optional;

@Service
public class MLWorkerTunnelService {
    private static final Logger log = LoggerFactory.getLogger(MLWorkerTunnelService.class);
    private final ApplicationProperties applicationProperties;
    private Channel tunnelServerChannel;

    public Optional<Integer> tunnelPort = Optional.empty();


    public MLWorkerTunnelService(ApplicationProperties applicationProperties) {
        this.applicationProperties = applicationProperties;
    }

    @PostConstruct
    private void init() throws Exception {
        if (applicationProperties.isExternalMlWorkerEnabled()) {
            this.tunnelServerChannel = listenForTunnelConnections(
                applicationProperties.getExternalMlWorkerEntrypointPort()
            );
        }
    }


    private Channel listenForTunnelConnections(int externalMlWorkerEntrypointPort) throws Exception {
        EventLoopGroup group = new NioEventLoopGroup();
        ServerBootstrap b = new ServerBootstrap();
        OuterChannelInitializer initializer = new OuterChannelInitializer();
        b.group(group)
            .channel(NioServerSocketChannel.class)
            .localAddress(new InetSocketAddress(externalMlWorkerEntrypointPort))
            .childHandler(initializer);
        initializer.eventBus.register(new EventListener() {
            @Subscribe
            public void onInnerServerStarted(InnerServerStartResponse event) {
                tunnelPort = Optional.of(event.port());
            }
        });
        ChannelFuture f = b.bind().sync();
        log.info("Listening for ML Worker tunnel connections on port {}", externalMlWorkerEntrypointPort);
        f.channel().closeFuture().addListener(future -> {
            log.info("Shutting down ML Worker tunnel");
            group.shutdownGracefully();
        });
        return f.channel();
    }
}
