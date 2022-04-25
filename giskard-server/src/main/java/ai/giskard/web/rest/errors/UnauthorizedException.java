
package ai.giskard.web.rest.errors;

import lombok.Getter;

public class UnauthorizedException extends BadRequestAlertException {

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

    public UnauthorizedException(String actionType, Entity entity) {
        super(String.format("Unauthorized: %s %s not possible  for your role", actionType, entity.getName()), entity.name().toLowerCase(), "accesscontrolerror");
    }
}
