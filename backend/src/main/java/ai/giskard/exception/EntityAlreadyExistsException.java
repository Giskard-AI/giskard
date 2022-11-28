package ai.giskard.exception;

public class EntityAlreadyExistsException extends IllegalArgumentException {
    public EntityAlreadyExistsException(String message) {
        super(message);
    }
}
