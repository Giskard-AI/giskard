package ai.giskard.web.dto.ml;

import ai.giskard.ml.dto.MLWorkerWSTestMessageType;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;

@Getter
@Setter
@NoArgsConstructor
public class TestResultMessageDTO implements Serializable {
    MLWorkerWSTestMessageType type;
    String text;

    public TestResultMessageDTO(MLWorkerWSTestMessageType type, String text) {
        this.type = type;
        this.text = text;
    }
}
