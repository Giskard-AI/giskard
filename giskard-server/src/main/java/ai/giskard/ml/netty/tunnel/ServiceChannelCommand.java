package ai.giskard.ml.netty.tunnel;

public enum ServiceChannelCommand {

    START_INNER_SERVER((byte) 0),
    REGISTER_CLIENT_CHANNEL((byte) 1);

    public final byte code;

    ServiceChannelCommand(byte i) {
        this.code = i;
    }
}
