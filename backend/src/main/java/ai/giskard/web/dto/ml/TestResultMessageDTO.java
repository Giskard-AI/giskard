package ai.giskard.web.dto.ml;

import ai.giskard.ml.dto.MLWorkerWSTestMessageType;
import ai.giskard.worker.TestMessageType;
import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;

@Getter
@Setter
public class TestResultMessageDTO implements Serializable {
    TestMessageType type;
    String text;

    public TestResultMessageDTO(TestMessageType type, String text) {
        this.type = type;
        this.text = text;
    }

    public TestResultMessageDTO(MLWorkerWSTestMessageType type, String text) {
        this.type = TestMessageType.forNumber(type.ordinal());
        this.text = text;
    }
}
