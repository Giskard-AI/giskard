package ai.giskard.repository;

import ai.giskard.domain.Feedback;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FeedbackRepository extends JpaRepository<Feedback, Long> {
    List<Feedback> findAllByProjectId(Long projectId);

    List<Feedback> findAllByDatasetId(String datasetId);

    List<Feedback> findAllByModelId(String modelId);

    List<Feedback> findAllByProjectIdAndUserId(Long projectId, Long userId);

    Feedback findOneById(Long feedbackId);


}
