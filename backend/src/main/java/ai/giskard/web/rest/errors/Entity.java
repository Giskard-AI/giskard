package ai.giskard.web.rest.errors;

import lombok.Getter;

public enum Entity {
    PROJECT("Project"),
    DATASET("Dataset"),
    PROJECT_MODEL("Model"),
    TEST_SUITE("Test suite"),
    TEST_FUNCTION("Test function"),
    SLICING_FUNCTION("Slicing function"),
    TRANSFORMATION_FUNCTION("Transformation function"),
    TEST("Test"),
    USER("User"),
    ROLE("Role"),
    FEEDBACK("Feedback"),
    FEEDBACK_REPLY("Feedback reply"),
    INSPECTION("Inspection");

    @Getter
    private final String name;

    Entity(String name) {
        this.name = name;
    }
}
