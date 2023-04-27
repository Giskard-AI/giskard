package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.web.dto.FunctionInputDTO;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Date;
import java.util.List;

@Getter
@UIModel
@Setter
@NoArgsConstructor
public class TestSuiteExecutionDTO {
    private Long id;
    private Long suiteId;
    private List<FunctionInputDTO> inputs;
    @UINullable
    private TestResult result;
    @UINullable
    private String message;
    @UINullable
    private String logs;
    @UINullable
    private List<SuiteTestExecutionDTO> results;

    private Date executionDate;
    private Date completionDate;
}
