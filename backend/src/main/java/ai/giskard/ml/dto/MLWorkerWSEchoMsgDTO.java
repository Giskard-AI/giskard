package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSEchoMsgDTO implements MLWorkerWSBaseDTO {
    private String msg;
}
