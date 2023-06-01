package ai.giskard.web.dto;

import ai.giskard.web.dto.user.UserMinimalDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.Instant;

@UIModel
@Getter
@AllArgsConstructor
public class FeedbackReplyDTO {
    private Long id;
    private Long feedbackId;
    private UserMinimalDTO user;
    private Long replyToReply;
    private String content;
    private Instant createdOn;
}
