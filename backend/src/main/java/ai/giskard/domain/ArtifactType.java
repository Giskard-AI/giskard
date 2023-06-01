package ai.giskard.domain;

public enum ArtifactType {
    MODEL,
    DATASET;

    public static ArtifactType fromDirectoryName(String directoryName) {
        return switch (directoryName.toLowerCase()) {
            case "models" -> MODEL;
            case "datasets" -> DATASET;
            default ->
                throw new IllegalArgumentException("Invalid artifact type, possible values are: 'models', 'datasets'");
        };
    }

    public String toDirectoryName() {
        return this.name().toLowerCase() + "s";
    }
}
