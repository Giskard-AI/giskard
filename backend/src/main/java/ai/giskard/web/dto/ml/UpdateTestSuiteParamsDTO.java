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
    private Long referenceDatasetId;
    private Long actualDatasetId;
    private Long modelId;
}
