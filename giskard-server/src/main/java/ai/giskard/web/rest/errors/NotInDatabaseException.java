package ai.giskard.web.rest.errors;

import lombok.Getter;

public class NotInDatabaseException extends BadRequestAlertException {

    public enum Entity {
        PROJECT("Project"),
        PROJECT_MODEL("Model"),
        TEST_SUITE("Test suite"),
        TEST("Test"),
        USER("User");

        @Getter
        private final String name;

        Entity(String name) {
            this.name = name;
        }
    }

    public NotInDatabaseException(Entity entity, String key) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not in database: %d", entity.getName(), key), entity.name().toLowerCase(), "accesscontrolerror");
    }
}
