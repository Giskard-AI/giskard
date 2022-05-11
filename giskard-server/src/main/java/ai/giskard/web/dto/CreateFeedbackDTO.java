package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@UIModel
@AllArgsConstructor
public class CreateFeedbackDTO {
    private Long projectId;
    private Long modelId;
    private Long datasetId;
    private String targetFeature;
    private String feedbackType;
    @UINullable
    private String featureName;
    @UINullable
    private String featureValue;
    @UINullable
    private String feedbackChoice;
    @UINullable
    private String feedbackMessage;
    private String userData;
    private String originalData;
}
