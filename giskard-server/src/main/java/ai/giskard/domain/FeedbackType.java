package ai.giskard.domain;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonValue;

@UIModel
public enum FeedbackType {
    VALUE_PERTURBATION("value perturbation"),
    VALUE("value"),
    GENERAL("general"),
    TARGET("target");

    private final String name;

    @JsonValue
    public String getName() {
        return name;
    }

    FeedbackType(String name) {
        this.name = name;
    }
}
