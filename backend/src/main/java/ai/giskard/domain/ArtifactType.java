package ai.giskard.domain;

public enum ArtifactType {
    MODEL,
    DATASET,
    TEST;

    public static ArtifactType fromDirectoryName(String directoryName) {
        return switch (directoryName.toLowerCase()) {
            case "models" -> MODEL;
            case "datasets" -> DATASET;
            case "tests" -> TEST;
            default ->
                throw new IllegalArgumentException("Invalid artifact type, possible values are: 'models', 'datasets', 'tests'");
        };
    }

    public String toDirectoryName() {
        return this.name().toLowerCase() + "s";
    }
}
