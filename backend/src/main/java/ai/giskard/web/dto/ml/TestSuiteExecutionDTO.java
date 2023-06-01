package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestResult;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.Map;

@Getter
@UIModel
@Setter
@NoArgsConstructor
public class TestSuiteExecutionDTO extends WorkerJobDTO {
    Long suiteId;
    private Map<String, String> inputs;
    @UINullable
    TestResult result;
    @UINullable
    private List<SuiteTestExecutionDTO> results;

}
