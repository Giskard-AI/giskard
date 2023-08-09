package ai.giskard.exception;

import ai.giskard.ml.dto.MLWorkerWSErrorDTO;
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

    public MLWorkerIllegalReplyException(MLWorkerWSErrorDTO error) {
        super(error.getErrorStr());
        this.errorType = error.getErrorType() + ": " + error.getErrorStr();
        this.errorString = error.getDetail();
    }
}
