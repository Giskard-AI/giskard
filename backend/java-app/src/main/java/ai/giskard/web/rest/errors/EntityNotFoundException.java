package ai.giskard.web.rest.errors;

import lombok.Getter;

public class EntityNotFoundException extends BadRequestAlertException {

    public enum Entity {
        PROJECT("Project"),
        PROJECT_MODEL("Model"),
        TEST_SUITE("Test suite"),
        TEST("Test");

        @Getter
        private final String name;

        Entity(String name) {
            this.name = name;
        }
    }

    public EntityNotFoundException(Entity entity, Long id) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not found by id: %d", entity.getName(), id), entity.name().toLowerCase(), "entitynotfound");
    }
}
