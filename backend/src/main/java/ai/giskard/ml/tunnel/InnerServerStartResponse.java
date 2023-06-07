package ai.giskard.ml.tunnel;

import com.google.common.util.concurrent.SettableFuture;
import io.netty.channel.Channel;
import io.netty.channel.EventLoopGroup;

import java.net.SocketAddress;

public record InnerServerStartResponse(
    SocketAddress localAddress,
    SettableFuture<Channel> innerChannelFuture,
    EventLoopGroup group
) {

}
