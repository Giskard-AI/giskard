package ai.giskard.ml.dto;

import lombok.Getter;

@Getter
public class MLWorkerWSTestMessageDTO {
    private MLWorkerWSTestMessageType type;

    private String text;
}
