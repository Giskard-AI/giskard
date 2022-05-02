package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.Dataset;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Temporary, the dataset can handle these properties
 */
@Getter
@Setter
@NoArgsConstructor
public class DatasetDetailsDTO {
    private int numberOfRows;
    private String[] headers;
}
