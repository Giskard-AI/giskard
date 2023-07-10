package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSRunModelForDataFrameDTO implements MLWorkerWSBaseDTO {
    @JsonProperty("all_predictions")
    private MLWorkerWSDataFrameDTO allPredictions;

    List<String> prediction;

    List<Float> probabilities;

    @JsonProperty("raw_prediction")
    List<Float> raw_Prediction;
}
