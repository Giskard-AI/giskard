package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

import java.io.Serial;

public class LoginAlreadyUsedException extends GiskardException {

    @Serial
    private static final long serialVersionUID = 1L;

    public LoginAlreadyUsedException() {
        super(HttpStatus.BAD_REQUEST);
    }
}
