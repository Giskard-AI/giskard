package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.ml.dto.MLWorkerWSRunAdHocTestDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Getter
@Setter
@UIModel
public class TestTemplateExecutionResultDTO {
    private UUID testUuid;
    private TestResult status;
    private List<NamedSingleTestResultDTO> result;
    private String message;
    private Instant executionDate;

    public TestTemplateExecutionResultDTO(UUID testUuid) {
        this.testUuid = testUuid;
    }

    public void setResult(MLWorkerWSRunAdHocTestDTO message) {
        result = message.getResults().stream().map(NamedSingleTestResultDTO::new).toList();
    }
}
