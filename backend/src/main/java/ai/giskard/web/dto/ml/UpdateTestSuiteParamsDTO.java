package ai.giskard.web.dto.ml;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class UpdateTestSuiteParamsDTO {
    private Long testId;
    private Long testSuiteId;
    private String referenceDatasetId;
    private String actualDatasetId;
    private String modelId;
}
