package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;

@UIModel
public enum PredictionType {
    REGRESSION,
    MULTICLASS_CLASSIFICATION,
    BINARY_CLASSIFICATION;
}
