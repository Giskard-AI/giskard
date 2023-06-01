package ai.giskard.web.dto;

import ai.giskard.web.dto.user.UserMinimalDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@UIModel
@Getter
@Setter
@NoArgsConstructor
public class FeedbackReplyDTO {
    private Long id;
    private Long feedbackId;
    private UserMinimalDTO user;
    private Long replyToReply;
    private String content;
    private Instant createdOn;
}
