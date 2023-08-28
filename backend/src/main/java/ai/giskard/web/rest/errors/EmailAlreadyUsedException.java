package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

import java.io.Serial;

public class EmailAlreadyUsedException extends GiskardException {

    @Serial
    private static final long serialVersionUID = 1L;

    public EmailAlreadyUsedException() {
        super(HttpStatus.BAD_REQUEST, "Email is already in use!");
    }
}
