package ai.giskard.web.dto.ml;

import ai.giskard.worker.TestMessageType;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;

@Getter
@Setter
@NoArgsConstructor
public class TestResultMessageDTO implements Serializable {
    TestMessageType type;
    String text;

    public TestResultMessageDTO(TestMessageType type, String text) {
        this.type = type;
        this.text = text;
    }
}
