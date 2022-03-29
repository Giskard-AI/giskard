package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.worker.TestResultMessage;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.stream.Collectors;

@Getter
@Setter
@NoArgsConstructor
public class TestExecutionResultDTO {
    private TestResult status;
    private List<NamedSingleTestResultDTO> result;
    private String message;

    public void setResult(TestResultMessage message) {
        result = message.getResultsList().stream().map(NamedSingleTestResultDTO::new).collect(Collectors.toList());
    }
}
