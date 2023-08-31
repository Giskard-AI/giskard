package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

@Getter
public class MLWorkerWSGeneratedTestInputDTO implements MLWorkerWSBaseDTO {
    private String name;

    private String value;

    @JsonProperty("is_alias")
    private Boolean isAlias;
}
