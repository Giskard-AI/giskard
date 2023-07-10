package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSArtifactRefDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("project_key")
    String projectKey;

    String id;

    Boolean sample;
}
