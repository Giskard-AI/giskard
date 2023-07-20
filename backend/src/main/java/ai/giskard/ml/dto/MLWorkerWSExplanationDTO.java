package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

import java.util.Map;

@Getter
public class MLWorkerWSExplanationDTO {
    @JsonProperty("per_feature")
    private Map<String, Float> perFeature;
}
