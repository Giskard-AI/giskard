package ai.giskard.exception;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import lombok.Getter;

@Getter
public class MLWorkerException extends StatusRuntimeException {
    private final String errorClass;
    private final String message;
    private final String stack;


    public MLWorkerException(Status status, String errorClass, String message, String stack) {
        super(status);
        this.errorClass = errorClass;
        this.message = message;
        this.stack = stack;
    }
}
