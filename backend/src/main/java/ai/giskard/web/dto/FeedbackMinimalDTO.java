package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class FeedbackMinimalDTO {
    private Long id;
    private String userLogin;
    private String modelName;
    private String datasetName;
    private UUID modelId;
    private UUID datasetId;
    private Instant createdOn;
    private String feedbackType;
    private String featureName;
    private String featureValue;
    private String feedbackChoice;
    private String feedbackMessage;
}
