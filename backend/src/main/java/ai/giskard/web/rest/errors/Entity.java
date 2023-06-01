package ai.giskard.web.rest.errors;

import lombok.Getter;

public enum Entity {
    PROJECT("Project"),
    DATASET("Dataset"),
    PROJECT_MODEL("Model"),
    TEST_SUITE("Test suite"),
    TEST_FUNCTION("Test function"),
    TEST("Test"),
    USER("User"),
    ROLE("Role"),
    FEEDBACK("Feedback"),
    INSPECTION("Inspection");

    @Getter
    private final String name;

    Entity(String name) {
        this.name = name;
    }
}
