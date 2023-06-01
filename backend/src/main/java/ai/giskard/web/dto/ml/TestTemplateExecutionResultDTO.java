package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.worker.TestResultMessage;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;
import java.util.List;

@Getter
@Setter
@UIModel
public class TestTemplateExecutionResultDTO {
    private String testId;
    private TestResult status;
    private List<NamedSingleTestResultDTO> result;
    private String message;
    private Instant executionDate;

    public TestTemplateExecutionResultDTO(String testId) {
        this.testId = testId;
    }

    public void setResult(TestResultMessage message) {
        result = message.getResultsList().stream().map(NamedSingleTestResultDTO::new).toList();
    }
}
