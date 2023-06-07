package ai.giskard.domain.ml;

public enum ModelType {
    CLASSIFICATION, REGRESSION, TEXT_GENERATION;

    public String getSimplifiedName() {
        return this.name().toLowerCase();
    }
}
