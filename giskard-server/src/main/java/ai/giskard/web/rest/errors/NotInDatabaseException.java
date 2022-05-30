package ai.giskard.web.rest.errors;

public class NotInDatabaseException extends BadRequestAlertException {

    public NotInDatabaseException(Entity entity, String key) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not in database: %s", entity.getName(), key), entity.name().toLowerCase(), "accesscontrolerror");
    }
}
