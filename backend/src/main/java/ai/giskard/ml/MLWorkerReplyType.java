package ai.giskard.ml;

import com.fasterxml.jackson.annotation.JsonIgnore;

public enum MLWorkerReplyType {
    FINISH(0),  // FINISH is always used by the newest message
    UPDATE(1);  // UPDATE is for replacement of old message

    @JsonIgnore
    private final int value;
    MLWorkerReplyType(int i) {
        value = i;
    }
}
