package ai.giskard.web.rest.errors;

import lombok.Getter;

public enum Entity {
    PROJECT("Project"),
    PROJECT_MODEL("Model"),
    TEST_SUITE("Test suite"),
    TEST("Test"),
    USER("User"),
    ROLE("Role");

    @Getter
    private final String name;

    Entity(String name) {
        this.name = name;
    }
}
