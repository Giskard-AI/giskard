package ai.giskard.web.dto.ml;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

/**
 * Temporary, the dataset can handle these properties
 */
@Getter
@Setter
@NoArgsConstructor
public class DatasetDetailsDTO {
    private int numberOfRows;
    private List<String> columns;
}
