package ai.giskard.web.rest.errors;

import lombok.Getter;

public class EntityNotFoundException extends BadRequestAlertException {

    public EntityNotFoundException(Entity entity, Long id) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not found by id: %d", entity.getName(), id), entity.name().toLowerCase(), "entitynotfound");
    }
}
