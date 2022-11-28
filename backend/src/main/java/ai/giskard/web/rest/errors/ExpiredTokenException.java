package ai.giskard.web.rest.errors;

import org.zalando.problem.AbstractThrowableProblem;
import org.zalando.problem.Status;

public class ExpiredTokenException extends AbstractThrowableProblem { // NOSONAR
    public ExpiredTokenException() {
        super(ErrorConstants.DEFAULT_TYPE, Status.UNAUTHORIZED.getReasonPhrase(), Status.UNAUTHORIZED,
            "Access token is expired, create a new one or re-login");
    }
}
