package ai.giskard.domain.ml;

public enum ModelType {
    CLASSIFICATION, REGRESSION;

    public String getSimplifiedName() {
        return this.name().toLowerCase();
    }
}
