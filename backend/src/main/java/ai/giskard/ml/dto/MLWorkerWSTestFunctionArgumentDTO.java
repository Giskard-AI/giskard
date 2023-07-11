package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

@Getter
public class MLWorkerWSTestFunctionArgumentDTO implements MLWorkerWSBaseDTO {
    String name;

    String type;

    Boolean optional;

    @JsonProperty("default")
    String defaultValue;

    Integer argOrder;
}
