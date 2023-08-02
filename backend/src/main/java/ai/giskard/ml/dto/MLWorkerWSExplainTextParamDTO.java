package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@Builder
public class MLWorkerWSExplainTextParamDTO implements MLWorkerWSBaseDTO {
    private MLWorkerWSArtifactRefDTO model;

    @JsonProperty("feature_name")
    private String featureName;

    private Map<String, String> columns;

    @JsonProperty("column_types")
    private Map<String, String> columnTypes;
}
