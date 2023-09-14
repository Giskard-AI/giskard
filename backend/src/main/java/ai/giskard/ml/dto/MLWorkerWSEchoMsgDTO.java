package ai.giskard.ml.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.jackson.Jacksonized;

@Getter
@Setter
@Builder
@Jacksonized
public class MLWorkerWSEchoMsgDTO implements MLWorkerWSBaseDTO {
    private String msg;
}
