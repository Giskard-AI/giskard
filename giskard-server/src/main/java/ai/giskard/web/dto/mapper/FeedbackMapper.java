package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Feedback;
import ai.giskard.domain.FeedbackReply;
import ai.giskard.web.dto.*;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Mappings;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = "spring", unmappedTargetPolicy = ReportingPolicy.IGNORE, uses = {GiskardMapper.class})
public interface FeedbackMapper {
    FeedbackDTO feedbackToFeedbackDTO(Feedback feedback);

    @Mappings({
        @Mapping(source = "user.login", target = "userLogin"),
        @Mapping(source = "model.name", target = "modelName"),
        @Mapping(source = "dataset.name", target = "datasetName"),
        @Mapping(source = "model.fileName", target = "modelFilename"),
        @Mapping(source = "dataset.fileName", target = "datasetFilename")
    })
    FeedbackMinimalDTO feedbackToFeedbackMinimalDTO(Feedback feedback);

    @Mappings({
        @Mapping(source = "projectId", target = "project.id"),
        @Mapping(source = "modelId", target = "model.id"),
        @Mapping(source = "datasetId", target = "dataset.id"),
    })
    Feedback createFeedbackDTOtoFeedback(CreateFeedbackDTO dto);

    FeedbackReply createFeedbackReplyDTOtoFeedbackReply(CreateFeedbackReplyDTO dto);

    @Mappings({
        @Mapping(source = "feedback.id", target = "feedbackId"),
    })
    FeedbackReplyDTO feedbackReplyToFeedbackReplyDTO(FeedbackReply feedbackReply);

    List<FeedbackMinimalDTO> feedbacksToFeedbackMinimalDTOs(List<Feedback> feedbacks);
}
