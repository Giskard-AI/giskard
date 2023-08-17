package ai.giskard.ml;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class MLWorkerReplyMessage {
    private int index;
    private int total;

    private String message;

    private MLWorkerReplyType type;
}
