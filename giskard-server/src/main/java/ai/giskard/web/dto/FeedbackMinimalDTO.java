package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.time.LocalDateTime;

@Getter
@AllArgsConstructor
@UIModel
public class FeedbackMinimalDTO {
    private Long id;
    private String userLogin;
    private String modelName;
    private String datasetName;
    private String modelFilename;
    private String datasetFilename;
    private Instant createdOn;
    private String feedbackType;
    private String featureName;
    private String featureValue;
    private String feedbackChoice;
    private String feedbackMessage;
}
