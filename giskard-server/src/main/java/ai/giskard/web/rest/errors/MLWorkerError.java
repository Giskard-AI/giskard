package ai.giskard.web.rest.errors;

import org.zalando.problem.AbstractThrowableProblem;
import org.zalando.problem.Status;

import java.net.URI;

public class MLWorkerError extends AbstractThrowableProblem { //NOSONAR: ok to have deep inheritance
    public MLWorkerError(URI errorConstantURI, io.grpc.Status.Code code, String message, String detail) {
        super(errorConstantURI, message, translateGRPCStatusCode(code), detail);
    }

    public static Status translateGRPCStatusCode(io.grpc.Status.Code code) {
        return switch (code) {
            case UNAVAILABLE -> Status.SERVICE_UNAVAILABLE;
            default -> Status.BAD_REQUEST;
        };
    }
}
