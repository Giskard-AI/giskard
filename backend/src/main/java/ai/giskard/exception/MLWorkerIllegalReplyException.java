package ai.giskard.exception;

import lombok.Getter;

@Getter
public class MLWorkerIllegalReplyException extends RuntimeException {

    private final String errorString;
    private final String errorType;

    public MLWorkerIllegalReplyException(String errorType, String errorString) {
        super(errorString);
        this.errorType = errorType;
        this.errorString = errorString;
    }
}
