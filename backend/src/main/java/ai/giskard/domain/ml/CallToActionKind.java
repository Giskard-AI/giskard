package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonValue;

@UIModel
public enum CallToActionKind {
    NONE,
    CREATE_SLICE,
    CREATE_TEST,
    CREATE_PERTURBATION,
    SAVE_PERTURBATION,
    CREATE_ROBUSTNESS_TEST,
    CREATE_SLICE_OPEN_DEBUGGER,
    OPEN_DEBUGGER_BORDERLINE,
    ADD_TEST_TO_CATALOG,
    SAVE_EXAMPLE,
    OPEN_DEBUGGER_OVERCONFIDENCE,
    CREATE_UNIT_TEST;

    @JsonValue
    public int toValue() {
        return ordinal();
    }
}
