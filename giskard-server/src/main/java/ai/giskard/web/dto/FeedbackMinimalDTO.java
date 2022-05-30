package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.Instant;

@Getter
@AllArgsConstructor
@UIModel
public class FeedbackMinimalDTO {
    private Long id;
    private String userLogin;
    private String modelName;
    private String datasetName;
    private Long modelId;
    private Long datasetId;
    private Instant createdOn;
    private String feedbackType;
    private String featureName;
    private String featureValue;
    private String feedbackChoice;
    private String feedbackMessage;
}
