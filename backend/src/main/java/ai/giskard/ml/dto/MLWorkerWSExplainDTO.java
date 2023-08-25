package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.Map;

@Getter
public class MLWorkerWSExplainDTO implements MLWorkerWSBaseDTO {
    private Map<String, MLWorkerWSExplanationDTO> explanations;
}
