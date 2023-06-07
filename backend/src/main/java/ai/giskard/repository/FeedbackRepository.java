package ai.giskard.repository;

import ai.giskard.domain.Feedback;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface FeedbackRepository extends MappableJpaRepository<Feedback, Long> {
    List<Feedback> findAllByProjectId(Long projectId);

    List<Feedback> findAllByDatasetId(UUID datasetId);

    List<Feedback> findAllByModelId(UUID modelId);

    List<Feedback> findAllByProjectIdAndUserId(Long projectId, Long userId);

    Feedback findOneById(Long feedbackId);


}
