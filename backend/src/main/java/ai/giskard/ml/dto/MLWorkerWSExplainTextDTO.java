package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;
import java.util.Map;

@Getter
public class MLWorkerWSExplainTextDTO implements MLWorkerWSBaseDTO {
    private List<String> words;

    private Map<String, MLWorkerWSWeightsPerFeatureDTO> weights;
}
