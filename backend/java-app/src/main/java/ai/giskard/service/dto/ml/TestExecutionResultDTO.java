package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.worker.TestResultMessage;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.HashMap;
import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
public class TestExecutionResultDTO {
    private TestResult status;
    private Map<String, SingleTestResultDTO> result;
    private String message;

    public void setResult(TestResultMessage message){
        result = new HashMap<>();
        message.getResultsMap().forEach((key, value) -> {
            result.put(key, new SingleTestResultDTO(value));
        });
    }
}
