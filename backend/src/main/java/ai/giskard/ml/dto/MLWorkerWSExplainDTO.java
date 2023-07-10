package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

import java.util.Map;

@Getter
public class MLWorkerWSExplainDTO implements MLWorkerWSBaseDTO {
    Map<String, MLWorkerWSExplanationDTO> explanations;
}
