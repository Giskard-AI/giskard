package ai.giskard.repository;

import ai.giskard.domain.FeedbackReply;
import org.springframework.stereotype.Repository;

@Repository
public interface FeedbackReplyRepository extends MappableJpaRepository<FeedbackReply, Long> {
    FeedbackReply findOneById(Long feedbackReplyId);
}
