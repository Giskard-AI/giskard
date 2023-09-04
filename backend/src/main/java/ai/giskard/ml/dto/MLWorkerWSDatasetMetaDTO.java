package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSDatasetMetaDTO {
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private String target;
}
