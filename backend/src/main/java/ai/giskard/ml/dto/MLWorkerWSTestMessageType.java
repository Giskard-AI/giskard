package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonIgnore;

public enum MLWorkerWSTestMessageType {
    ERROR(0),
    INFO(1);

    @JsonIgnore
    private final int value;
    MLWorkerWSTestMessageType(int i) {
        value = i;
    }
}
