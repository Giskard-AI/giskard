package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.CreatedDate;

import javax.persistence.*;
import java.time.Instant;

@Getter
@Entity(name = "feedback_replies")
public class FeedbackReply extends BaseEntity{
    @Setter
    @ManyToOne
    private Feedback feedback;

    @Setter
    @ManyToOne
    private User user;

    @Setter
    private Long replyToReply;
    @Setter
    private String content;

    @CreatedDate
    @Column(name = "created_on", updatable = false)
    private Instant createdOn = Instant.now();

}
