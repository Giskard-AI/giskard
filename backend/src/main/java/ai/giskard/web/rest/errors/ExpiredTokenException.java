package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

public class ExpiredTokenException extends GiskardException {

    public ExpiredTokenException() {
        super(HttpStatus.UNAUTHORIZED, "Expired token");
    }
}
