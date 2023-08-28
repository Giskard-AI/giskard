package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonValue;

@UIModel
public enum CallToActionKind {
    None,
    CreateSlice,
    CreateTest,
    CreatePerturbation,
    SavePerturbation,
    CreateRobustnessTest,
    CreateSliceOpenDebugger,
    OpenDebuggerBorderline,
    AddTestToCatalog,
    SaveExample,
    OpenDebuggerOverconfidence,
    CreateUnitTest;

    @JsonValue
    public int toValue() {
        return ordinal();
    }
}
