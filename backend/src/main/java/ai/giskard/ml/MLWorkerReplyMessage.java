package ai.giskard.ml;

import lombok.Builder;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Builder
public class MLWorkerReplyMessage {
    private int index;

    private String message;

    private MLWorkerReplyType type;
}
