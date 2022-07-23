package ai.giskard.service;

public class GiskardRuntimeException extends RuntimeException {
    public GiskardRuntimeException(String message, Throwable cause) {
        super(message, cause);
    }
    public GiskardRuntimeException(String message) {
        super(message);
    }
}
