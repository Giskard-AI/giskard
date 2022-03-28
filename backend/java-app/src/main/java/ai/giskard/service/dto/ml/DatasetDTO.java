package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.Dataset;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@Getter
@Setter
@NoArgsConstructor
public class DatasetDTO {
    @NotNull
    private Long id;
    @NotNull
    private String name;
    @NotNull
    private Long projectId;

    public DatasetDTO(Dataset dataset) {
        this.id = dataset.getId();
        this.name = dataset.getName();
        this.projectId = dataset.getProject().getId();
    }
}
