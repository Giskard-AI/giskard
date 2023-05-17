package ai.giskard.repository;

import ai.giskard.domain.Feedback;
import ai.giskard.domain.FeedbackReply;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FeedbackReplyRepository extends MappableJpaRepository<FeedbackReply, Long> {
    FeedbackReply findOneById(Long feedbackReplyId);

    List<FeedbackReply> findAllByFeedback(Feedback feedback);

    List<FeedbackReply> findAllByReplyToReply(Long feedbackReplyId);

}
