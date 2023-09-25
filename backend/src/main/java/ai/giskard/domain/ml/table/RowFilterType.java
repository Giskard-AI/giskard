package ai.giskard.domain.ml.table;

import com.dataiku.j2ts.annotations.UIModel;

@UIModel
public enum RowFilterType {
    ALL,
    WRONG,
    CORRECT,
    BORDERLINE,
    OVERCONFIDENCE,
    CUSTOM
}
