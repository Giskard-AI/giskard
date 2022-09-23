package ai.giskard.ml.netty.tunnel;

import com.google.common.util.concurrent.SettableFuture;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import lombok.SneakyThrows;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.util.SocketUtils;

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import static ai.giskard.ml.netty.tunnel.ServiceChannelCommand.REGISTER_CLIENT_CHANNEL;


public class OuterChannelInitializer extends ChannelInitializer<SocketChannel> {
    Set<ChannelId> serviceChannelsIds = new HashSet<>();
    Map<String, SettableFuture<Channel>> outerChannelByInnerChannelId = new HashMap<>();
    private final Map<ChannelId, String> innerChannelIdByOuterChannel = new HashMap<>();
    private final Map<String, Channel> innerChannelById = new HashMap<>();

    private static class InnerServerStartResponse {
        final SettableFuture<Channel> innerChannelFuture;
        final EventLoopGroup group;

        private InnerServerStartResponse(SettableFuture<Channel> innerChannelFuture, EventLoopGroup group) {
            this.innerChannelFuture = innerChannelFuture;
            this.group = group;
        }
    }

    private final Logger log = LoggerFactory.getLogger(OuterChannelInitializer.class);
    private InnerServerStartResponse innerServerData;

    private void initInnerServer(SocketChannel outerChannel) {
        this.innerServerData = startInnerServer(outerChannel);
    }

    @Override
    protected void initChannel(SocketChannel outerChannel) {
        log.info("New outer connection, outer channel id {}", outerChannel.id());

        ChannelPipeline pipeline = outerChannel.pipeline();
        pipeline.addLast(
            new ChannelInboundHandlerAdapter() {
                @Override
                public void channelInactive(ChannelHandlerContext ctx) throws Exception {
                    log.debug("Outer channel inactive {}", ctx.channel().id());
                    if (serviceChannelsIds.contains(ctx.channel().id())) {
                        log.info("Shutting down inner server for outer channel {}", ctx.channel().id());
                        innerServerData.group.shutdownGracefully().sync();
                        serviceChannelsIds.remove(ctx.channel().id());
                    }
                }

                @Override
                public void channelRead(ChannelHandlerContext ctx, Object msg) {
                    ChannelId channelId = ctx.channel().id();
                    ByteBuf in = (ByteBuf) msg;
                    if (innerChannelIdByOuterChannel.containsKey(channelId)) {
                        Channel innerChannel = innerChannelById.get(innerChannelIdByOuterChannel.get(channelId));
                        log.debug("Outer->Inner: Writing {} bytes from {} to {}", in.readableBytes(), channelId, innerChannel.id());
                        innerChannel.writeAndFlush(msg);
                    } else {
                        if (in.readableBytes() >= 5) {
                            int payloadLength = in.readInt() - 1;
                            byte messageType = in.readByte();
                            ByteBuf payload = null;
                            if (in.readableBytes() > 0) {
                                payload = in.readBytes(payloadLength);
                            }
                            switch (messageType) {
                                case 0 -> {
                                    serviceChannelsIds.add(channelId);
                                    initInnerServer(outerChannel);
                                }
                                case 1 -> {
                                    String innerChannelId = payload.toString(StandardCharsets.UTF_8);
                                    outerChannelByInnerChannelId.get(innerChannelId).set(outerChannel);
                                    innerChannelIdByOuterChannel.put(channelId, innerChannelId);
                                    log.info("Linked outer channel {} with inner channel {}", outerChannel.id(), innerChannelId);
                                }
                                default -> throw new RuntimeException("Unknown command");
                            }
                        }
                    }
                }
            });
    }

    /**
     * Checks if a channel serves as a communication channel (transfers GRPC messages)
     * or as a service channel (transfers Giskard service messages to create other communication channels)
     */
    private boolean isDataChannel(Channel channel) {
        return innerChannelIdByOuterChannel.containsKey(channel.id());
    }

    private InnerServerStartResponse startInnerServer(SocketChannel serviceOuterChannel) {

        final SettableFuture<Channel> innerChannelFuture = SettableFuture.create();
        int innerPort = SocketUtils.findAvailableTcpPort();

        ChannelInitializer<SocketChannel> childHandler = new ChannelInitializer<>() {
            @Override
            protected void initChannel(SocketChannel ch) {
                ChannelPipeline pipeline = ch.pipeline();
                pipeline.addLast(
                    new ChannelInboundHandlerAdapter() {
                        @Override
                        public void channelInactive(ChannelHandlerContext ctx) throws Exception {
                            super.channelInactive(ctx);
                            log.info("Connection to inner server closed, channel id {}", ctx.channel().id());
                            Channel outerChannel = outerChannelByInnerChannelId.remove(ctx.channel().id().asShortText()).get();
                            innerChannelIdByOuterChannel.remove(outerChannel.id());
                            outerChannel.close();

                        }

                        @Override
                        public void channelActive(ChannelHandlerContext ctx) {
                            Channel innerChannel = ctx.channel();
                            String innerChannelShortName = innerChannel.id().asShortText();
                            log.info("New connection to inner server, channel id {}", ctx.channel().id());

                            innerChannelById.put(innerChannelShortName, innerChannel);
                            innerChannelFuture.set(innerChannel);

                            SettableFuture<Channel> outerChannelFuture = SettableFuture.create();
                            outerChannelByInnerChannelId.put(innerChannelShortName, outerChannelFuture);

                            callRegisterClientChannel(innerChannelShortName);
                        }

                        private void callRegisterClientChannel(String innerChannelShortName) {
                            ByteBuf out = Unpooled.buffer();
                            out.writeBytes(Unpooled.copiedBuffer(innerChannelShortName, StandardCharsets.UTF_8));
                            out.writeByte(REGISTER_CLIENT_CHANNEL.code);
                            log.info("Linking inner channel {} with new outer channel through service channel {}", innerChannelShortName, serviceOuterChannel.id());
                            serviceOuterChannel.writeAndFlush(out);
                        }

                        @SneakyThrows
                        @Override
                        public void channelRead(ChannelHandlerContext ctx, Object msg) {
                            Channel outerChannel = outerChannelByInnerChannelId.get(ctx.channel().id().asShortText()).get();
                            ByteBuf in = (ByteBuf) msg;
                            int originalLength = in.readableBytes();
                            log.debug("Inner->Outer: Writing {} bytes from {} to {}", originalLength, ch.id(), outerChannel.id());

                            outerChannel.writeAndFlush(in);
                        }
                    });
            }
        };


        SocketAddress address = new InetSocketAddress(innerPort);
        EventLoopGroup group = new NioEventLoopGroup();
        ChannelFuture bindFuture = new ServerBootstrap()
            .group(group, group)
            .channel(NioServerSocketChannel.class)
            .childHandler(childHandler)
            .localAddress(innerPort)
            .bind();
        try {
            bindFuture.await();
        } catch (InterruptedException ex) {
            throw new RuntimeException("bind interrutped", ex);
        }
        if (!bindFuture.isSuccess()) {
            throw new RuntimeException("bind failed", bindFuture.cause());
        }
        log.info("Started inner server {} for incoming service channel {}", address, serviceOuterChannel.id());

        return new InnerServerStartResponse(innerChannelFuture, group);

    }

}
