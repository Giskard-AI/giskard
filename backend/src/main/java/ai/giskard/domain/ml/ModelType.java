package ai.giskard.domain.ml;

public enum ModelType {
    CLASSIFICATION, REGRESSION, LLM;

    public String getSimplifiedName() {
        return this.name().toLowerCase();
    }
}
