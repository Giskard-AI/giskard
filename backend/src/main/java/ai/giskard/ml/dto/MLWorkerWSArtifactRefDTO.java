package ai.giskard.ml.dto;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;
import lombok.NonNull;
import lombok.Setter;
import lombok.extern.jackson.Jacksonized;

@Getter
@Setter
@Builder
@Jacksonized
public class MLWorkerWSArtifactRefDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("project_key")
    private String projectKey;

    private String id;

    private Boolean sample;

    public static MLWorkerWSArtifactRefDTO fromModel(@NonNull ProjectModel model) {
        return MLWorkerWSArtifactRefDTO.builder()
            .projectKey(model.getProject().getKey())
            .id(model.getId().toString()).build();
    }

    public static MLWorkerWSArtifactRefDTO fromDataset(@NonNull Dataset dataset) {
        return MLWorkerWSArtifactRefDTO.builder()
            .projectKey(dataset.getProject().getKey())
            .id(dataset.getId().toString()).build();
    }

    public static MLWorkerWSArtifactRefDTO fromDataset(@NonNull Dataset dataset, boolean sample) {
        return MLWorkerWSArtifactRefDTO.builder()
            .projectKey(dataset.getProject().getKey())
            .id(dataset.getId().toString())
            .sample(sample).build();
    }
}
