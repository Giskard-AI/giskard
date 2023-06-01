package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Feedback;
import ai.giskard.domain.FeedbackReply;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.utils.JSON;
import ai.giskard.web.dto.*;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = "spring", unmappedTargetPolicy = ReportingPolicy.ERROR, uses = {
    GiskardMapper.class,
    DatasetRepository.class,
    ModelRepository.class,
    ProjectRepository.class,
    JSON.class
})
public interface FeedbackMapper {
    FeedbackDTO feedbackToFeedbackDTO(Feedback feedback);

    @Mapping(source = "user.login", target = "userLogin")
    @Mapping(source = "model.name", target = "modelName")
    @Mapping(source = "dataset.name", target = "datasetName")
    @Mapping(source = "model.id", target = "modelId")
    @Mapping(source = "dataset.id", target = "datasetId")
    FeedbackMinimalDTO feedbackToFeedbackMinimalDTO(Feedback feedback);

    @Mapping(source = "projectId", target = "project")
    @Mapping(source = "modelId", target = "model")
    @Mapping(source = "datasetId", target = "dataset")
    @Mapping(target = "user", ignore = true)
    @Mapping(target = "feedbackReplies", ignore = true)
    Feedback createFeedbackDTOtoFeedback(CreateFeedbackDTO dto);

    @Mapping(target = "user", ignore = true)
    @Mapping(target = "feedback", ignore = true)
    FeedbackReply createFeedbackReplyDTOtoFeedbackReply(CreateFeedbackReplyDTO dto);

    @Mapping(source = "feedback.id", target = "feedbackId")
    FeedbackReplyDTO feedbackReplyToFeedbackReplyDTO(FeedbackReply feedbackReply);

    List<FeedbackMinimalDTO> feedbacksToFeedbackMinimalDTOs(List<Feedback> feedbacks);
}
