package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSWeightsPerFeatureDTO implements MLWorkerWSBaseDTO {
    List<Float> weights;
}
