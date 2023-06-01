package ai.giskard.repository;

import ai.giskard.domain.FeedbackReply;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface FeedbackReplyRepository extends JpaRepository<FeedbackReply, Long> {
}
