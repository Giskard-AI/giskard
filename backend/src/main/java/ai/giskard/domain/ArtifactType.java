package ai.giskard.domain;

public enum ArtifactType {
    MODEL,
    DATASET,
    TEST,
    SLICE;

    public static ArtifactType fromDirectoryName(String directoryName) {
        return switch (directoryName.toLowerCase()) {
            case "models" -> MODEL;
            case "datasets" -> DATASET;
            case "tests" -> TEST;
            case "slices" -> SLICE;
            default -> throw new IllegalArgumentException(
                "Invalid artifact type, possible values are: 'models', 'datasets', 'tests', 'slices'"
            );
        };
    }

    public String toDirectoryName() {
        return this.name().toLowerCase() + "s";
    }
}
