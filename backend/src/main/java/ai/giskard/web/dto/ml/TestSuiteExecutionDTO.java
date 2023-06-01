package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestResult;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.EnumType;
import javax.persistence.Enumerated;
import java.util.Date;
import java.util.Map;

@Getter
@UIModel
@Setter
@NoArgsConstructor
public class TestSuiteExecutionDTO {
    Long suiteId;
    Date executionDate;
    @Enumerated(EnumType.STRING)
    TestResult result;
    private Map<String, SingleTestResultDTO> results;

}
