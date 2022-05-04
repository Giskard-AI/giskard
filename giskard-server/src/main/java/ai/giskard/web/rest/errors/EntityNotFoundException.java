package ai.giskard.web.rest.errors;

public class EntityNotFoundException extends BadRequestAlertException {

    public EntityNotFoundException(Entity entity, Long id) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not found by id: %d", entity.getName(), id), entity.name().toLowerCase(), "entitynotfound");
    }

    public EntityNotFoundException(Entity entity, String key) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not found by key: %s", entity.getName(), key), entity.name().toLowerCase(), "entitynotfound");
    }

}
