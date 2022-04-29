package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.Dataset;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DatasetDTO extends FileDTO {

    public DatasetDTO(Dataset dataset) {
        this.id = dataset.getId();
        this.fileName = dataset.getName();
    }
}
