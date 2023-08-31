package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonValue;

@UIModel
public enum PushKind {
    INVALID,
    PERTURBATION,
    CONTRIBUTION,
    OVERCONFIDENCE,
    BORDERLINE;

    @JsonValue
    public int toValue() {
        return ordinal();
    }
}
