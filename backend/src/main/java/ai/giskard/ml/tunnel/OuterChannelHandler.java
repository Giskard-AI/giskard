package ai.giskard.ml.tunnel;

import ai.giskard.event.UpdateWorkerStatusEvent;
import ai.giskard.service.ml.MLWorkerDataEncryptor;
import ai.giskard.service.ml.MLWorkerSecurityService;
import com.google.common.eventbus.EventBus;
import com.google.common.util.concurrent.SettableFuture;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.buffer.ByteBuf;
import io.netty.channel.*;
import io.netty.channel.local.LocalAddress;
import io.netty.channel.local.LocalServerChannel;
import io.netty.channel.socket.SocketChannel;
import io.netty.handler.logging.ByteBufFormat;
import io.netty.handler.logging.LogLevel;
import io.netty.handler.logging.LoggingHandler;
import lombok.Getter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationEventPublisher;

import javax.crypto.SecretKey;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.UUID;

import static ai.giskard.ml.tunnel.ServiceChannelCommand.REGISTER_CLIENT_CHANNEL;
import static ai.giskard.ml.tunnel.ServiceChannelCommand.START_INNER_SERVER;

@ChannelHandler.Sharable
public class OuterChannelHandler extends ChannelInboundHandlerAdapter {
    private ApplicationEventPublisher applicationEventPublisher;
    private final Logger log = LoggerFactory.getLogger(OuterChannelHandler.class);

    private Optional<InnerServerStartResponse> innerServerData = Optional.empty();

    private final MLWorkerSecurityService mlWorkerSecurityService;

    private final ChannelRegistry channelRegistry = new ChannelRegistry();


    @Getter
    private EventBus eventBus = new EventBus();

    public OuterChannelHandler(MLWorkerSecurityService mlWorkerSecurityService, ApplicationEventPublisher applicationEventPublisher) {
        this.mlWorkerSecurityService = mlWorkerSecurityService;
        this.applicationEventPublisher = applicationEventPublisher;
    }

    private void initInnerServer(SocketChannel outerChannel, String keyId) {
        this.innerServerData = Optional.of(startInnerServer(outerChannel, keyId));
        eventBus.post(this.innerServerData);
    }


    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        ChannelId channelId = ctx.channel().id();
        log.debug("Outer channel inactive {}", channelId);

        if (!channelRegistry.isServiceChannel(channelId)) {
            channelRegistry.getInnerChannelByOuterChannelId(channelId).ifPresent(innerChannel -> {
                try {
                    innerChannel.close().sync();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    log.error("Interrupted while stopping inner channel {}", innerChannel.id());
                }
            });
        }
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        log.error("Caught exception in outer server handler", cause);
        Channel outerChannel = ctx.channel();
        ctx.close().addListener(future -> log.info("Service channel connection is lost: {}", outerChannel.id()));

        channelRegistry.getInnerChannelByOuterChannelId(outerChannel.id()).ifPresent(innerChannel ->
            innerChannel.close().addListener(
                future -> log.info("Closed inner channel {} linked to closed outer channel {}", outerChannel.id(), innerChannel.id()))
        );
    }

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        SocketChannel outerChannel = (SocketChannel) ctx.channel();
        ByteBuf in = (ByteBuf) msg;
        log.debug("Outer: Writing {} bytes from {}", in.readableBytes(), outerChannel.id());
        if (channelRegistry.isDataChannel(outerChannel.id())) {
            passDataDirectly(in, outerChannel);
        } else {
            handleServiceChannelInput(ctx, outerChannel, in);
        }
    }

    private void handleServiceChannelInput(ChannelHandlerContext ctx, SocketChannel outerChannel, ByteBuf in) {
        DecryptionResult decrypted = mlWorkerSecurityService.decryptWithKeyHeader(in);
        in = decrypted.getData();

        byte messageType = in.readByte();
        ByteBuf payload = null;
        if (in.readableBytes() > 0) {
            payload = in.readBytes(in.readableBytes());
        }

        handleServiceCommand(outerChannel, messageType, payload, decrypted.getKeyId());
    }

    private void handleServiceCommand(SocketChannel outerChannel, byte messageType, ByteBuf payload, String keyId) {
        switch (messageType) {
            case START_INNER_SERVER -> {
                channelRegistry.addServiceChannelId(outerChannel.id());

                initInnerServer(outerChannel, keyId);

                mlWorkerSecurityService.findKey(keyId).setUsed(true);
            }
            case REGISTER_CLIENT_CHANNEL -> {
                assert payload != null;
                String innerChannelId = payload.toString(StandardCharsets.UTF_8);
                channelRegistry.linkOuterAndInnerChannels(outerChannel, innerChannelId, mlWorkerSecurityService.findKey(keyId));
                log.debug("Linked outer channel {} with inner channel {}", outerChannel.id(), innerChannelId);
            }
            default -> throw new IllegalArgumentException("Unknown command");
        }
    }


    private void passDataDirectly(ByteBuf in, SocketChannel outerChannel) {
        channelRegistry.getInnerChannelByOuterChannelId(outerChannel.id()).ifPresent(innerChannel -> {
            log.debug("Outer->Inner: Writing {} bytes from {} to {}", in.readableBytes(), outerChannel.id(), innerChannel.id());
            SecretKey key = channelRegistry.getOuterChannelKey(outerChannel.id()).getKey();

            ByteBuf msg = new MLWorkerDataEncryptor(key).decryptPayload(in);
            if (msg.readableBytes() != 0) {
                innerChannel.writeAndFlush(msg);
            }
        });
    }


    private InnerServerStartResponse startInnerServer(SocketChannel serviceOuterChannel, String keyId) {
        final SettableFuture<Channel> innerChannelFuture = SettableFuture.create();
        EventLoopGroup group = new DefaultEventLoopGroup();

        SocketAddress localAddress = new LocalAddress(UUID.randomUUID().toString());

        ChannelInitializer<Channel> innerChannelHandler = new ChannelInitializer<>() {
            @Override
            protected void initChannel(Channel ch) {
                ChannelPipeline pipeline = ch.pipeline();
                pipeline.addLast(
                    new LoggingHandler("Inner channel", LogLevel.DEBUG, ByteBufFormat.SIMPLE),
                    new InnerChannelHandler(
                        serviceOuterChannel,
                        channelRegistry,
                        innerChannelFuture,
                        keyId
                    ));
            }
        };
        ChannelFuture bindFuture = new ServerBootstrap()
            .group(group)
            .channel(LocalServerChannel.class)
            .childHandler(innerChannelHandler)
            .localAddress(localAddress)
            .bind();

        bindFuture.addListener(future -> {
            if (future.isSuccess()) {
                log.info("Started inner server {} for incoming service channel {}", localAddress, serviceOuterChannel.id());
            }
            applicationEventPublisher.publishEvent(new UpdateWorkerStatusEvent(this, true));
        });
        serviceOuterChannel.closeFuture().addListener(future -> {
            log.info("Shutting down inner server for outer channel {}", serviceOuterChannel.id());
            group.shutdownGracefully();
            mlWorkerSecurityService.removeKey(keyId);
            channelRegistry.removeServiceChannel(serviceOuterChannel.id());
            innerServerData = Optional.empty();
            eventBus.post(innerServerData);
            applicationEventPublisher.publishEvent(new UpdateWorkerStatusEvent(this, false));
        });

        return new InnerServerStartResponse(localAddress, innerChannelFuture, group);
    }
}
