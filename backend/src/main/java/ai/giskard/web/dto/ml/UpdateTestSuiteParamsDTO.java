package ai.giskard.web.dto.ml;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class UpdateTestSuiteParamsDTO {
    private Long testId;
    private Long testSuiteId;
    private Long referenceDatasetId;
    private Long actualDatasetId;
    private Long modelId;
}
