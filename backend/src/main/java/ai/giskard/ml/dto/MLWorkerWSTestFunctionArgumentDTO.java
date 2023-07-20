package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

@Getter
public class MLWorkerWSTestFunctionArgumentDTO implements MLWorkerWSBaseDTO {
    private String name;

    private String type;

    private Boolean optional;

    @JsonProperty("default")
    private String defaultValue;

    private Integer argOrder;
}
