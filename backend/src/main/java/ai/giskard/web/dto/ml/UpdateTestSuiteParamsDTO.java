package ai.giskard.web.dto.ml;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
public class UpdateTestSuiteParamsDTO {
    private Long testId;
    private Long testSuiteId;
    private UUID referenceDatasetId;
    private UUID actualDatasetId;
    private UUID modelId;
}
