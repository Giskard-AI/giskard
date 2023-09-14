package ai.giskard.ml.dto;

import ai.giskard.ml.MLWorkerReplyType;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

@Getter
public class MLWorkerReplyDTO {
    private String id;

    private String action;

    private String payload;

    @JsonProperty(defaultValue = "0")
    private int index = 0;

    @JsonProperty(defaultValue = "1")
    private int total = 1;

    @JsonProperty(value = "f_index")
    private int fragmentIndex = 0;  // Fragment index

    @JsonProperty(value = "f_count")
    private int fragmentCount = 1;  // Fragment count

    private MLWorkerReplyType type = MLWorkerReplyType.FINISH;
}
