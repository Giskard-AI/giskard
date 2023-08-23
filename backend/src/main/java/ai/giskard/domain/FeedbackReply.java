package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.CreatedDate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.ManyToOne;
import java.time.Instant;

@Getter
@Entity(name = "feedback_replies")
public class FeedbackReply extends BaseEntity{
    @Setter
    @ManyToOne
    @JsonBackReference
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
    @JsonIgnore
    private Instant createdOn = Instant.now();

}
