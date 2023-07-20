package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSWeightsPerFeatureDTO implements MLWorkerWSBaseDTO {
    private List<Float> weights;
}
