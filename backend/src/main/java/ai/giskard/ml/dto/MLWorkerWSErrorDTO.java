package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

@Getter
public class MLWorkerWSErrorDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("error_str")
    private String errorStr;

    @JsonProperty("error_type")
    private String errorType;

    private String detail;
}
