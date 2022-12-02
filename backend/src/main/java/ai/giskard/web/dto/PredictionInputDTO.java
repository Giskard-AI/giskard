package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class PredictionInputDTO {
    private Long datasetId;
    private Map<String, String> features;
}
