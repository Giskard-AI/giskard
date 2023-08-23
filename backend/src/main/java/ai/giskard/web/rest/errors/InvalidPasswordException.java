package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

public class InvalidPasswordException extends GiskardException {

    public InvalidPasswordException() {
        super(HttpStatus.BAD_REQUEST, "Invalid password");
    }
}
