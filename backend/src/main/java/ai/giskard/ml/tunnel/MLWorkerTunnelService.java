package ai.giskard.ml.tunnel;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.service.ml.MLWorkerSecurityService;
import com.google.common.eventbus.Subscribe;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.LengthFieldBasedFrameDecoder;
import io.netty.handler.logging.ByteBufFormat;
import io.netty.handler.logging.LogLevel;
import io.netty.handler.logging.LoggingHandler;
import lombok.Getter;
import lombok.Setter;
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
    public static final int LENGTH_FIELD_LENGTH_BYTES = 4;
    private final ApplicationProperties applicationProperties;
    private final MLWorkerSecurityService mlWorkerSecurityService;

    @Getter
    private Optional<InnerServerStartResponse> innerServerDetails = Optional.empty();
    @Getter
    @Setter
    private boolean clearCacheRequested = true;

    public MLWorkerTunnelService(
        ApplicationProperties applicationProperties,
        MLWorkerSecurityService mlWorkerSecurityService) {
        this.applicationProperties = applicationProperties;
        this.mlWorkerSecurityService = mlWorkerSecurityService;
    }

    @PostConstruct
    private void init() {
        if (applicationProperties.isExternalMlWorkerEnabled()) {
            listenForTunnelConnections(applicationProperties.getExternalMlWorkerEntrypointPort());
        }
    }

    private Channel listenForTunnelConnections(int externalMlWorkerEntrypointPort) {
        EventLoopGroup group = new NioEventLoopGroup();
        ServerBootstrap b = new ServerBootstrap();

        OuterChannelHandler outerChannelHandler = new OuterChannelHandler(mlWorkerSecurityService);
        ChannelInitializer<SocketChannel> outerChannelInitializer = new ChannelInitializer<>() {
            @Override
            protected void initChannel(SocketChannel outerChannel) {
                log.info("New outer connection, outer channel id {}", outerChannel.id());

                outerChannel.pipeline().addLast(
                    new LoggingHandler("Outer channel", LogLevel.DEBUG, ByteBufFormat.SIMPLE),
                    new LengthFieldBasedFrameDecoder(Integer.MAX_VALUE, 0, LENGTH_FIELD_LENGTH_BYTES, 0, LENGTH_FIELD_LENGTH_BYTES),
                    outerChannelHandler
                );
            }
        };

        b.group(group)
            .channel(NioServerSocketChannel.class)
            .localAddress(new InetSocketAddress(externalMlWorkerEntrypointPort))
            .childHandler(outerChannelInitializer);

        outerChannelHandler.getEventBus().register(new EventListener() {
            @Subscribe
            public void onInnerServerStarted(Optional<InnerServerStartResponse> event) {
                innerServerDetails = event;
                clearCacheRequested = true;
            }
        });
        ChannelFuture f = b.bind().addListener(future -> {
            if (future.isSuccess()) {
                log.info("Listening for ML Worker tunnel connections on port {}", externalMlWorkerEntrypointPort);
            }
        });
        f.channel().closeFuture().addListener(future -> {
            log.info("Shutting down ML Worker tunnel");
            group.shutdownGracefully();
        });
        return f.channel();
    }
}
