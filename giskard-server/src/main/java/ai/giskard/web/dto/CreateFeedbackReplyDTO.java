package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@UIModel
@AllArgsConstructor
public class CreateFeedbackReplyDTO {
    private String content;
    private Integer replyToReply;
}
