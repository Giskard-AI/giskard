package ai.giskard.web.dto.ml;

import ai.giskard.web.dto.SuiteTestDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class TestExecutionDto {

    private SuiteTestDTO test;
    private List<TestResultMessageDTO> messages;
    private List<Integer> actualSlicesSize;
    private List<Integer> referenceSlicesSize;
    private boolean passed;
    private List<Integer> partialUnexpectedIndexList;
    private List<Integer> unexpectedIndexList;
    private Integer missingCount;
    private Double missingPercent;
    private Integer unexpectedCount;
    private Double unexpectedPercent;
    private Double unexpectedPercentTotal;
    private Double unexpectedPercentNonmissing;
    private float metric;

}
