package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;

@UIModel
public enum RowFilter {
    ALL,
    WRONG,
    CORRECT,
    CUSTOM
}
