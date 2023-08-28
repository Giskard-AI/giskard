package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSSuiteInputDTO implements MLWorkerWSBaseDTO {
    private String name;

    private String type;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    @JsonProperty("model_meta")
    private MLWorkerWSModelMetaDTO modelMeta;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    @JsonProperty("dataset_meta")
    private MLWorkerWSDatasetMetaDTO datasetMeta;
}
