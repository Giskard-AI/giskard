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

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import static ai.giskard.ml.netty.tunnel.ServiceChannelCommand.REGISTER_CLIENT_CHANNEL;


public class OuterChannelInitializer extends ChannelInitializer<SocketChannel> {
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
                public void channelRead(ChannelHandlerContext ctx, Object msg) {
                    ByteBuf in = (ByteBuf) msg;
                    if (innerChannelIdByOuterChannel.containsKey(ctx.channel().id())) {
                        Channel innerChannel = innerChannelById.get(innerChannelIdByOuterChannel.get(outerChannel.id()));
                        //log.debug("Outer->Outer: Writing {} bytes from {} to {}", in.readableBytes(), outerChannel.id(), innerChannel.id());
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
                                    initInnerServer(outerChannel);
                                }
                                case 1 -> {
                                    String innerChannelId = payload.toString(StandardCharsets.UTF_8);
                                    outerChannelByInnerChannelId.get(innerChannelId).set(outerChannel);
                                    innerChannelIdByOuterChannel.put(outerChannel.id(), innerChannelId);
                                }
                                default -> throw new RuntimeException("Unknown command");
                            }
                        }
                    }
                }
            });
    }

    private boolean isDataChannel(Channel channel) {
        return innerChannelIdByOuterChannel.containsKey(channel.id());
    }

    private InnerServerStartResponse startInnerServer(SocketChannel mainOuterChannel) {

        final SettableFuture<Channel> innerChannelFuture = SettableFuture.create();
        //SocketUtils.findAvailableTcpPort()
        int innerPort = 11222;

        ChannelInitializer<SocketChannel> childHandler = new ChannelInitializer<>() {
            @Override
            protected void initChannel(SocketChannel ch) {
                ChannelPipeline pipeline = ch.pipeline();
                pipeline.addLast(
                    new ChannelInboundHandlerAdapter() {
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
                            mainOuterChannel.writeAndFlush(out);
                        }

                        @SneakyThrows
                        @Override
                        public void channelRead(ChannelHandlerContext ctx, Object msg) {
                            Channel outerChannel = outerChannelByInnerChannelId.get(ctx.channel().id().asShortText()).get();
                            ByteBuf in = (ByteBuf) msg;
                            //int originalLength = in.readableBytes();
                            //log.debug("Inner->Outer: Writing {} bytes from {} to {}", originalLength, ch.id(), outerChannel.id());

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
        log.info("Started inner server {} for incoming channel {}", address, mainOuterChannel.id());

        return new InnerServerStartResponse(innerChannelFuture, group);

    }

}
