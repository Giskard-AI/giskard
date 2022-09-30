package ai.giskard.ml.tunnel;

import com.google.common.util.concurrent.SettableFuture;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelId;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.socket.SocketChannel;
import lombok.SneakyThrows;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.util.Map;

import static ai.giskard.ml.tunnel.ServiceChannelCommand.REGISTER_CLIENT_CHANNEL;

public class InnerChannelHandler extends ChannelInboundHandlerAdapter {
    private final Logger log = LoggerFactory.getLogger(InnerChannelHandler.class);
    private final SocketChannel serviceOuterChannel;
    private final Map<String, SettableFuture<Channel>> outerChannelByInnerChannelId;
    private final Map<ChannelId, String> innerChannelIdByOuterChannel;
    private final Map<String, Channel> innerChannelById;
    private final SettableFuture<Channel> innerChannelFuture;

    public InnerChannelHandler(SocketChannel serviceOuterChannel, Map<String,
        SettableFuture<Channel>> outerChannelByInnerChannelId, Map<ChannelId,
        String> innerChannelIdByOuterChannel, Map<String, Channel> innerChannelById,
                               SettableFuture<Channel> innerChannelFuture) {
        this.serviceOuterChannel = serviceOuterChannel;
        this.outerChannelByInnerChannelId = outerChannelByInnerChannelId;
        this.innerChannelIdByOuterChannel = innerChannelIdByOuterChannel;
        this.innerChannelById = innerChannelById;
        this.innerChannelFuture = innerChannelFuture;
    }

    @Override
    public void channelRegistered(ChannelHandlerContext ctx) throws Exception {
        super.channelRegistered(ctx);
    }

    @Override
    public void channelInactive(ChannelHandlerContext ctx) throws Exception {
        super.channelInactive(ctx);
        log.info("Connection to inner server closed, channel id {}", ctx.channel().id());
        Channel outerChannel = outerChannelByInnerChannelId.remove(ctx.channel().id().asShortText()).get();
        outerChannel.close().sync();
        innerChannelIdByOuterChannel.remove(outerChannel.id());
        log.info("Closed outer channel {}", outerChannel.id());
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
        out.writeByte(REGISTER_CLIENT_CHANNEL);
        log.info("Linking inner channel {} with new outer channel through service channel {}", innerChannelShortName, serviceOuterChannel.id());
        serviceOuterChannel.writeAndFlush(out);
    }

    @SneakyThrows
    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        Channel outerChannel = outerChannelByInnerChannelId.get(ctx.channel().id().asShortText()).get();
        ByteBuf in = (ByteBuf) msg;
        int originalLength = in.readableBytes();
        log.debug("Inner->Outer: Writing {} bytes from {} to {}", originalLength, ctx.channel().id(), outerChannel.id());

        outerChannel.writeAndFlush(in);
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        log.error("Caught exception in inner server handler", cause);
        ctx.close();
    }
}
