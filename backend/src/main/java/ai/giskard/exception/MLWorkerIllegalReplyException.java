package ai.giskard.exception;

import ai.giskard.ml.dto.MLWorkerWSErrorDTO;
import lombok.Getter;

@Getter
public class MLWorkerIllegalReplyException extends RuntimeException {

    private final String errorString;
    private final String errorType;

    public static final String INVALID_RESPONSE_ERROR_TYPE = "Invalid response";

    public MLWorkerIllegalReplyException(String errorString) {
        super(errorString);
        this.errorType = INVALID_RESPONSE_ERROR_TYPE;
        this.errorString = errorString;
    }

    public MLWorkerIllegalReplyException(MLWorkerWSErrorDTO error) {
        super(error.getErrorStr() + "\n" + error.getDetail());
        this.errorType = error.getErrorType() + ": " + error.getErrorStr();
        this.errorString = error.getDetail();
    }
}
