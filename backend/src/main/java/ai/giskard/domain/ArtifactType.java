package ai.giskard.domain;

public enum ArtifactType {
    MODEL,
    DATASET,
    TEST,
    SLICE,
    TRANSFORMATION;

    public static ArtifactType fromDirectoryName(String directoryName) {
        return switch (directoryName.toLowerCase()) {
            case "models" -> MODEL;
            case "datasets" -> DATASET;
            case "tests" -> TEST;
            case "slices" -> SLICE;
            case "transformations" -> TRANSFORMATION;
            default -> throw new IllegalArgumentException(
                "Invalid artifact type, possible values are: 'models', 'datasets', 'tests', 'slices', 'transformations'"
            );
        };
    }

    public String toDirectoryName() {
        return this.name().toLowerCase() + "s";
    }
}
