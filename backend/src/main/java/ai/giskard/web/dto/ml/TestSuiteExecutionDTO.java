package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestResult;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Date;
import java.util.List;
import java.util.Map;

@Getter
@UIModel
@Setter
@NoArgsConstructor
public class TestSuiteExecutionDTO {
    Long suiteId;
    Date executionDate;

    private Map<String, String> inputs;
    TestResult result;
    private List<TestExecutionDto> results;

}
