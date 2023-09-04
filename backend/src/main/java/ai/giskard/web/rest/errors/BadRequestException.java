package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

public class BadRequestException extends GiskardException {
    public BadRequestException(String description) {
        super(HttpStatus.BAD_REQUEST, description);
    }
}
