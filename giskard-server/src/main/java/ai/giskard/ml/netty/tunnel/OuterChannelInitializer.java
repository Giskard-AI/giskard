package ai.giskard.ml.netty.tunnel;

import com.google.common.util.concurrent.SettableFuture;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.LengthFieldBasedFrameDecoder;
import org.apache.commons.codec.binary.Hex;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutionException;

public class OuterChannelInitializer extends ChannelInitializer<SocketChannel> {
    boolean withHeaders = false;

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


    @Override
    protected void initChannel(SocketChannel outerChannel) {
        log.info("New outer connection, outer channel id {}", outerChannel.id());

        this.innerServerData = startInnerServer(outerChannel);

        ChannelPipeline pipeline = outerChannel.pipeline();
        if (withHeaders) {
            pipeline.addLast(new LengthFieldBasedFrameDecoder(Integer.MAX_VALUE, 8, 4));
        }
        pipeline.addLast(
            //new LoggingHandler(LogLevel.DEBUG),
            new ChannelInboundHandlerAdapter() {
                @Override
                public void channelInactive(ChannelHandlerContext ctx) throws Exception {
                    log.info("Shutting down inner server");
                    innerServerData.group.shutdownGracefully().sync();
                }

                @Override
                public void channelRead(ChannelHandlerContext ctx, Object msg) {
                    try {
                        Channel innerChannel = innerServerData.innerChannelFuture.get();
                        ByteBuf in = (ByteBuf) msg;
                        int contentLength = 0;
                        if (withHeaders) {
                            String client = in.readBytes(8).toString(StandardCharsets.UTF_8);
                            int len = in.readInt();
                            contentLength = in.readableBytes();
                        }
                        log.debug("Outer->Inner: Writing {} bytes from {} to {} : {}", contentLength, ctx.channel().id(), "-", Hex.encodeHexString(in.nioBuffer()));
                        innerChannel.writeAndFlush(in);
                    } catch (ExecutionException | InterruptedException e) {
                        throw new RuntimeException(e);
                    }
                }
            });
    }

    private InnerServerStartResponse startInnerServer(SocketChannel outerChannel) {

        final SettableFuture<Channel> innerChannelFuture = SettableFuture.create();
        //int innerPort = findAvailableTcpPort();
        int innerPort = 11222;

        ChannelInitializer<SocketChannel> childHandler = new ChannelInitializer<>() {
            @Override
            protected void initChannel(SocketChannel ch) {
                ChannelPipeline pipeline = ch.pipeline();
                pipeline.addLast(
                    //new LoggingHandler(LogLevel.DEBUG),
                    new ChannelInboundHandlerAdapter() {
                        @Override
                        public void channelActive(ChannelHandlerContext ctx) throws Exception {
                            log.info("New connection to inner server, channel id {}", ch.id());
                            innerChannelFuture.set(ctx.channel());
                        }

                        @Override
                        public void channelRead(ChannelHandlerContext ctx, Object msg) {
                            ByteBuf in = (ByteBuf) msg;
                            int originalLength = in.readableBytes();
                            log.debug("Inner->Outer: Writing {} bytes from {} to {} : {}", originalLength, ch.id(), outerChannel.id(), Hex.encodeHexString(in.nioBuffer()));
                            if (withHeaders) {
                                outerChannel.write(Unpooled.copiedBuffer(ch.id().asShortText(), StandardCharsets.UTF_8));
                                outerChannel.write(Unpooled.copyInt(originalLength));
                            }
                            outerChannel.writeAndFlush(in);
                        }
                    });
            }
        };


        SocketAddress address = new InetSocketAddress(innerPort);
        //SocketAddress address = new LocalAddress("" + Math.random());
        EventLoopGroup group = new NioEventLoopGroup();
        //EventLoopGroup group = new DefaultEventLoop();
        ChannelFuture bindFuture = new ServerBootstrap()
            .group(group, group)
            .channel(NioServerSocketChannel.class)
            //.channel(LocalServerChannel.class)
            .childHandler(childHandler)
            .localAddress(innerPort)
            .bind();


        //ChannelFuture bindFuture = new ServerBootstrap()
        //    .group(group, group)
        //    //.channel(NioServerSocketChannel.class)
        //    .channel(LocalServerChannel.class)
        //    .childHandler(childHandler).bind(address);
        try {
            bindFuture.await();
        } catch (InterruptedException ex) {
            throw new RuntimeException("bind interrutped", ex);
        }
        if (!bindFuture.isSuccess()) {
            throw new RuntimeException("bind failed", bindFuture.cause());
        }
        log.info("Started inner server {} for incoming channel {}", address, outerChannel.id());


        //final ManagedChannel channel = NettyChannelBuilder.forAddress(address)
        //    .eventLoopGroup(group)
        //    .channelType(LocalChannel.class)
        //    .usePlaintext()
        //    .build();
        //
        //ConnectivityState state = channel.getState(true);
        //System.out.println(1);

        //final ManagedChannel channel = NettyChannelBuilder.forAddress(address)
        //    .eventLoopGroup(group)
        //    .channelType(LocalChannel.class)
        //    .usePlaintext()
        //    .build();
        //


        return new InnerServerStartResponse(innerChannelFuture, group);

    }

}
