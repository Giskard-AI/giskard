package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonValue;

@UIModel
public enum PushKind {
    Invalid,
    Perturbation,
    Contribution,
    Overconfidence,
    Borderline;

    @JsonValue
    public int toValue() {
        return ordinal();
    }
}
