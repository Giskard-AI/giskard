package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSPushActionDTO implements MLWorkerWSBaseDTO {

    @JsonProperty("object_uuid")
    private String objectUuid;
    
    private List<MLWorkerWSFuncArgumentDTO> arguments;
}
