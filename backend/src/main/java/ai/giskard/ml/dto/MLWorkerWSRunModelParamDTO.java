package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSRunModelParamDTO implements MLWorkerWSBaseDTO {
    MLWorkerWSArtifactRefDTO model;

    MLWorkerWSArtifactRefDTO dataset;

    Long inspectionId;

    @JsonProperty("project_key")
    String projectKey;
}
