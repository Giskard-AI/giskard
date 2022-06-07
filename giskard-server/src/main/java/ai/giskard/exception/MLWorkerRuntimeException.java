package ai.giskard.exception;

import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
public class MLWorkerRuntimeException extends StatusRuntimeException {
    @Setter
    private String message;
    private final String details;
    private final List<String> originalStack;


    public MLWorkerRuntimeException(Status status, String message, String details, List<String> originalStack) {
        super(status);
        this.message = message;
        this.details = details;
        this.originalStack = originalStack;
    }
}
