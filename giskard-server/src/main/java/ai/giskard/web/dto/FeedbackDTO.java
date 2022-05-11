package ai.giskard.web.dto;

import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.dto.ml.ProjectDTO;
import ai.giskard.web.dto.user.UserMinimalDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.Instant;
import java.util.Set;

@UIModel
@Getter
@AllArgsConstructor
public class FeedbackDTO {
    private Long id;
    private ProjectDTO project;
    private ModelDTO model;
    private DatasetDTO dataset;
    private UserMinimalDTO user;
    private Set<FeedbackReplyDTO> feedbackReplies;
    private String targetFeature;
    private Instant createdOn;
    private String feedbackType;
    private String featureName;
    private String featureValue;
    private String feedbackChoice;
    private String feedbackMessage;
    private String userData;
    private String originalData;
}
