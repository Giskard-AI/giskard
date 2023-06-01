package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@UIModel
@NoArgsConstructor
public class CreateFeedbackReplyDTO {
    private String content;
    private Integer replyToReply;
}
