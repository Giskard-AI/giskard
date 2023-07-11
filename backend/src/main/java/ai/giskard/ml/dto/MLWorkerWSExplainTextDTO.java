package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;
import java.util.Map;

@Getter
public class MLWorkerWSExplainTextDTO implements MLWorkerWSBaseDTO {
    List<String> words;

    Map<String, MLWorkerWSWeightsPerFeatureDTO> weights;
}
