package ai.giskard.ml.tunnel;

public class ServiceChannelCommand {
    private ServiceChannelCommand() {}

    public static final byte START_INNER_SERVER = 0;
    public static final byte REGISTER_CLIENT_CHANNEL = 1;
}
