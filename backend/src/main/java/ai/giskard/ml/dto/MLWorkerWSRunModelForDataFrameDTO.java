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

    private List<String> prediction;

    private List<Float> probabilities;

    @JsonProperty("raw_prediction")
    private List<Float> rawPrediction;
}
