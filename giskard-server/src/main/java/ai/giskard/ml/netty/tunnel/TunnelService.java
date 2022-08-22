/*
 * Copyright 2018, gRPC Authors All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package ai.giskard.ml.netty.tunnel;

import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.ChannelFuture;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.InetSocketAddress;

public class TunnelService {
    private static final Logger log = LoggerFactory.getLogger(TunnelService.class);
    private final int outerPort;

    public TunnelService(int outerPort) {
        this.outerPort = outerPort;
    }


    private ChannelFuture start() throws Exception {
        EventLoopGroup group = new NioEventLoopGroup();
        //try {
        ServerBootstrap b = new ServerBootstrap();
        b.group(group)
            .channel(NioServerSocketChannel.class)
            .localAddress(new InetSocketAddress(outerPort))
            .childHandler(new OuterChannelInitializer());
        ChannelFuture f = b.bind().sync();
        log.info("Started outer server on port {}", outerPort);
        return f.channel().closeFuture();
        //} finally {
        //    group.shutdownGracefully().sync();
        //}
    }

    public static void main(String[] args) throws Exception {
        TunnelService tunnel = new TunnelService(10050);
        tunnel.start().sync();
    }
}
