
package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

public class UnauthorizedException extends GiskardException {

    public UnauthorizedException(String actionType, Entity entity) {
        super(HttpStatus.UNAUTHORIZED, String.format("Unauthorized to %s %s", actionType, entity.getName()));
    }
}
