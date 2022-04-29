package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.Dataset;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class DatasetDTO extends FileDTO {

    public DatasetDTO(Dataset dataset) {
        this.id = dataset.getId();
        this.fileName = dataset.getFileName();
        this.name = dataset.getName();
    }
}
