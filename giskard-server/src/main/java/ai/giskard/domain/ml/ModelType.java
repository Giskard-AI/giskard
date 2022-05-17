package ai.giskard.domain.ml;

public enum ModelType {
    BINARY_CLASSIFICATION,
    MULTICLASS_CLASSIFICATION,
    REGRESSION;

    public boolean isClassification() {
        return isClassification(this);
    }

    public static boolean isClassification(ModelType type) {
        return type == BINARY_CLASSIFICATION || type == MULTICLASS_CLASSIFICATION;
    }
}
