package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.web.ErrorResponseException;

public class GiskardException extends ErrorResponseException {
    public GiskardException(HttpStatusCode status, String description) {
        super(status, ProblemDetail.forStatusAndDetail(status, description), null);
    }

    public GiskardException(HttpStatusCode status, Throwable th) {
        super(status, ProblemDetail.forStatus(status), th);
    }

    public GiskardException(HttpStatusCode status) {
        super(status);
    }
}
