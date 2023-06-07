package ai.giskard.ml.tunnel;

import ai.giskard.service.GiskardRuntimeException;
import ai.giskard.service.ml.MLWorkerSecretKey;
import com.google.common.util.concurrent.SettableFuture;
import io.netty.channel.Channel;
import io.netty.channel.ChannelId;
import io.netty.channel.socket.SocketChannel;

import java.util.*;
import java.util.concurrent.ExecutionException;

public class ChannelRegistry {
    private final Set<ChannelId> serviceChannelsIds = new HashSet<>();
    private final Map<ChannelId, String> innerChannelIdByOuterChannel = new HashMap<>();
    private final Map<ChannelId, MLWorkerSecretKey> outerChannelSecretKey = new HashMap<>();
    private final Map<String, Channel> innerChannelById = new HashMap<>();
    private final Map<String, SettableFuture<Channel>> outerChannelByInnerChannelId = new HashMap<>();

    public boolean isServiceChannel(ChannelId channelId) {
        return serviceChannelsIds.contains(channelId);
    }

    public void removeServiceChannel(ChannelId channelId) {
        serviceChannelsIds.remove(channelId);
    }

    public Optional<Channel> getInnerChannelByOuterChannelId(ChannelId channelId) {
        if (!innerChannelIdByOuterChannel.containsKey(channelId)) {
            return Optional.empty();
        }
        return Optional.ofNullable(innerChannelById.get(innerChannelIdByOuterChannel.get(channelId)));
    }

    public boolean isDataChannel(ChannelId channelId) {
        return innerChannelIdByOuterChannel.containsKey(channelId);
    }

    public void addServiceChannelId(ChannelId channelId) {
        serviceChannelsIds.add(channelId);
    }

    public void linkOuterAndInnerChannels(SocketChannel outerChannel, String innerChannelId, MLWorkerSecretKey key) {
        outerChannelByInnerChannelId.get(innerChannelId).set(outerChannel);
        innerChannelIdByOuterChannel.put(outerChannel.id(), innerChannelId);
        outerChannelSecretKey.put(outerChannel.id(), key);
    }

    public MLWorkerSecretKey getOuterChannelKey(ChannelId channelId) {
        return outerChannelSecretKey.get(channelId);
    }

    public void removeInnerChannel(ChannelId innerChannelId) {
        Channel outerChannel = getOuterChannelByInnerChannelId(innerChannelId);
        ChannelId outerChannelId = outerChannel.id();
        outerChannelByInnerChannelId.remove(innerChannelId.asShortText());
        innerChannelIdByOuterChannel.remove(outerChannelId);
        outerChannelSecretKey.remove(outerChannelId);
    }

    public Channel getOuterChannelByInnerChannelId(ChannelId channelId) {
        try {
            return outerChannelByInnerChannelId.get(channelId.asShortText()).get();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new GiskardRuntimeException("Interrupted while retrieving outer channel");
        } catch (ExecutionException e) {
            throw new GiskardRuntimeException("Failed to retrieve outer channel", e);
        }
    }

    public void addInnerChannel(Channel innerChannel) {
        String innerChannelShortName = innerChannel.id().asShortText();
        innerChannelById.put(innerChannelShortName, innerChannel);
        innerChannel.closeFuture().addListener(future -> innerChannelById.remove(innerChannelShortName));

        SettableFuture<Channel> outerChannelFuture = SettableFuture.create();
        outerChannelByInnerChannelId.put(innerChannelShortName, outerChannelFuture);

    }
}
