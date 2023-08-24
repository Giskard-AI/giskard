package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

public class NotInDatabaseException extends GiskardException {

    public NotInDatabaseException(Entity entity, String key) {
        super(HttpStatus.BAD_REQUEST, String.format("%s not in database: %s", entity.getName(), key));
    }
}
