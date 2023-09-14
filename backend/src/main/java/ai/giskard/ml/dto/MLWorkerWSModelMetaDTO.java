package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSModelMetaDTO implements MLWorkerWSBaseDTO {
    @JsonInclude(JsonInclude.Include.NON_NULL)
    @JsonProperty("model_type")
    private String modelType;
}
