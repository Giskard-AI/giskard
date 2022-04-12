package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;

@Entity
public class FeedbackReply {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;


    @Getter
    @Setter
    @ManyToOne
    private Feedback feedback;

    @Getter
    @Setter
    @ManyToOne
    private User user;

    @NotNull
    private int replyToReply;
    private String content;
    private LocalDateTime createdOn;

}
