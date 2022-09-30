package ai.giskard.ml.tunnel;

import com.google.common.eventbus.EventBus;
import com.google.common.util.concurrent.SettableFuture;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.buffer.ByteBuf;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.logging.LoggingHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.util.SocketUtils;

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.*;

import static ai.giskard.ml.tunnel.ServiceChannelCommand.REGISTER_CLIENT_CHANNEL;
import static ai.giskard.ml.tunnel.ServiceChannelCommand.START_INNER_SERVER;

public class OuterChannelHandler extends ChannelInboundHandlerAdapter {
    private final Logger log = LoggerFactory.getLogger(OuterChannelHandler.class);
    private final Set<ChannelId> serviceChannelsIds = new HashSet<>();
    private Optional<InnerServerStartResponse> innerServerData = Optional.empty();
    private final Map<ChannelId, String> innerChannelIdByOuterChannel = new HashMap<>();
    private final Map<String, Channel> innerChannelById = new HashMap<>();

    private final Map<String, SettableFuture<Channel>> outerChannelByInnerChannelId = new HashMap<>();
    public EventBus eventBus = new EventBus();


    private void initInnerServer(SocketChannel outerChannel) {
        this.innerServerData = Optional.of(startInnerServer(outerChannel));
        eventBus.post(this.innerServerData);
    }


    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        log.debug("Outer channel inactive {}", ctx.channel().id());
        if (serviceChannelsIds.contains(ctx.channel().id())) {
            log.info("Shutting down inner server for outer channel {}", ctx.channel().id());
            innerServerData.ifPresent(innerServerStartResponse -> innerServerStartResponse.group.shutdownGracefully());
            serviceChannelsIds.remove(ctx.channel().id());
            innerServerData = Optional.empty();
            eventBus.post(innerServerData);
        }
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        log.warn("Caught exception in outer server handler", cause);
        ctx.close();
    }

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        SocketChannel outerChannel = (SocketChannel) ctx.channel();
        ByteBuf in = (ByteBuf) msg;
        log.debug("Outer: Writing {} bytes from {}", in.readableBytes(), outerChannel.id());
        while (in.readableBytes() > 0) {
            if (innerChannelIdByOuterChannel.containsKey(outerChannel.id())) {
                Channel innerChannel = innerChannelById.get(innerChannelIdByOuterChannel.get(outerChannel.id()));
                log.debug("Outer->Inner: Writing {} bytes from {} to {}", in.readableBytes(), outerChannel.id(), innerChannel.id());
                ByteBuf data = in.readBytes(in.readableBytes());
                innerChannel.writeAndFlush(data);
            } else {
                // Giskard service messages have the following structure:
                // <message length = 4B><message type = 1B><optional payload = [message length - 1]B>
                if (in.readableBytes() < 5) {
                    continue;
                }
                int payloadLength = in.readInt() - 1;
                byte messageType = in.readByte();
                ByteBuf payload = null;
                if (payloadLength > 0 && in.readableBytes() >= payloadLength) {
                    payload = in.readBytes(payloadLength);
                }

                switch (messageType) {
                    case START_INNER_SERVER -> {
                        serviceChannelsIds.add(outerChannel.id());
                        initInnerServer(outerChannel);
                    }
                    case REGISTER_CLIENT_CHANNEL -> {
                        assert payload != null;
                        String innerChannelId = payload.toString(StandardCharsets.UTF_8);
                        outerChannelByInnerChannelId.get(innerChannelId).set(ctx.channel());
                        innerChannelIdByOuterChannel.put(outerChannel.id(), innerChannelId);
                        log.info("Linked outer channel {} with inner channel {}", ctx.channel().id(), innerChannelId);
                    }
                    default -> throw new IllegalArgumentException("Unknown command");
                }
            }
        }

    }


    private InnerServerStartResponse startInnerServer(SocketChannel serviceOuterChannel) {
        final SettableFuture<Channel> innerChannelFuture = SettableFuture.create();
        int innerPort = SocketUtils.findAvailableTcpPort();

        SocketAddress address = new InetSocketAddress(innerPort);
        EventLoopGroup group = new NioEventLoopGroup();
        ChannelFuture bindFuture = new ServerBootstrap()
            .group(group)
            .channel(NioServerSocketChannel.class)
            .childHandler(new ChannelInitializer<>() {
                @Override
                protected void initChannel(Channel ch) {
                    ChannelPipeline pipeline = ch.pipeline();
                    pipeline.addLast(
                        new LoggingHandler("Inner"),
                        new InnerChannelHandler(
                            serviceOuterChannel,
                            outerChannelByInnerChannelId,
                            innerChannelIdByOuterChannel,
                            innerChannelById,
                            innerChannelFuture
                        ));
                }
            })
            .localAddress(innerPort)
            .bind();

        bindFuture.addListener(future -> {
            if (future.isSuccess()) {
                log.info("Started inner server {} for incoming service channel {}", address, serviceOuterChannel.id());
            }
        });

        return new InnerServerStartResponse(innerPort, innerChannelFuture, group);
    }

    public record InnerServerStartResponse(
        int port,
        SettableFuture<Channel> innerChannelFuture,
        EventLoopGroup group
    ) {

    }
}
