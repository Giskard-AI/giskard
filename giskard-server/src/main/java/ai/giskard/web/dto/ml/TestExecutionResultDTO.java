package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.worker.TestResultMessage;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

@Getter
@Setter
@UIModel
public class TestExecutionResultDTO {
    private Long testId;
    private String testName;
    private TestResult status;
    private List<NamedSingleTestResultDTO> result;
    private String message;
    private Instant executionDate;

    public TestExecutionResultDTO(Long testId) {
        this.testId = testId;
    }

    public void setResult(TestResultMessage message) {
        result = message.getResultsList().stream().map(NamedSingleTestResultDTO::new).toList();
    }
}
