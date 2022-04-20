package ai.giskard.web.rest.errors;

import lombok.Getter;

public class EntityAccessControlException extends BadRequestAlertException {

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

    public EntityAccessControlException(Entity entity, Long id) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not accessible by id: %d", entity.getName(), id), entity.name().toLowerCase(), "accesscontrolerror");
    }
}
