package ai.giskard.ml.tunnel;

import ai.giskard.config.SpringContext;
import ai.giskard.service.ml.MLWorkerDataEncryptor;
import ai.giskard.service.ml.MLWorkerSecurityService;
import com.google.common.util.concurrent.SettableFuture;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufUtil;
import io.netty.buffer.Unpooled;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelId;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.socket.SocketChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;

import static ai.giskard.ml.tunnel.ServiceChannelCommand.REGISTER_CLIENT_CHANNEL;

public class InnerChannelHandler extends ChannelInboundHandlerAdapter {
    private final Logger log = LoggerFactory.getLogger(InnerChannelHandler.class);
    private final SocketChannel serviceOuterChannel;
    private final ChannelRegistry channelRegistry;
    private final SettableFuture<Channel> innerChannelFuture;
    private final MLWorkerDataEncryptor encryptor;

    public InnerChannelHandler(SocketChannel serviceOuterChannel,
                               ChannelRegistry channelRegistry,
                               SettableFuture<Channel> innerChannelFuture, String keyId) {
        this.serviceOuterChannel = serviceOuterChannel;
        this.channelRegistry = channelRegistry;
        this.innerChannelFuture = innerChannelFuture;
        this.encryptor = new MLWorkerDataEncryptor(SpringContext.getBean(MLWorkerSecurityService.class).findKey(keyId).getKey());
    }

    @Override
    public void channelInactive(ChannelHandlerContext ctx) throws Exception {
        super.channelInactive(ctx);
        ChannelId innerChannelId = ctx.channel().id();
        log.debug("Connection to inner server closed, channel id {}", innerChannelId);
        Channel outerChannel = channelRegistry.getOuterChannelByInnerChannelId(innerChannelId);
        outerChannel.close().sync();
        channelRegistry.removeInnerChannel(innerChannelId);
        log.info("Closed outer channel {}", outerChannel.id());
    }

    @Override
    public void channelActive(ChannelHandlerContext ctx) {
        Channel innerChannel = ctx.channel();
        String innerChannelShortName = innerChannel.id().asShortText();
        log.debug("New connection to inner server, channel id {}", ctx.channel().id());

        channelRegistry.addInnerChannel(innerChannel);
        innerChannelFuture.set(innerChannel);

        callRegisterClientChannel(innerChannelShortName);
    }

    private void callRegisterClientChannel(String innerChannelShortName) {
        ByteBuf out = Unpooled.buffer();
        out.writeBytes(Unpooled.copiedBuffer(innerChannelShortName, StandardCharsets.UTF_8));
        out.writeByte(REGISTER_CLIENT_CHANNEL);
        log.debug("Linking inner channel {} with new outer channel through service channel {}", innerChannelShortName, serviceOuterChannel.id());
        serviceOuterChannel.writeAndFlush(
            Unpooled.wrappedBuffer(encryptor.encrypt(ByteBufUtil.getBytes(out)))
        );
    }

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        Channel outerChannel = channelRegistry.getOuterChannelByInnerChannelId(ctx.channel().id());
        ByteBuf in = (ByteBuf) msg;
        int originalLength = in.readableBytes();

        if (originalLength != 0) {
            log.debug("Inner->Outer: Writing {} bytes from {} to {}", originalLength, ctx.channel().id(), outerChannel.id());
            byte[] bytes = encryptor.encrypt(ByteBufUtil.getBytes(in));
            outerChannel.writeAndFlush(Unpooled.wrappedBuffer(bytes));
        }
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        log.warn("Caught exception in inner server handler", cause);
        Channel outerChannel = channelRegistry.getOuterChannelByInnerChannelId(ctx.channel().id());
        ctx.close().addListener(future ->
            log.info("Inner channel is closed by exception {}: {}", ctx.channel().id(), cause.getMessage())
        );

        if (outerChannel.isOpen()) {
            outerChannel.close().addListener(future ->
                log.info("Outer channel {} is closed due to exception in inner channel {}: {}",
                    outerChannel.id(), ctx.channel().id(), cause.getMessage()));
        }
    }
}
