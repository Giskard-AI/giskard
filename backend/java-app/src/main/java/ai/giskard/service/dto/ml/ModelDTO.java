package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.ProjectModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ModelDTO {
    private Long id;
    private String name;
    private Long projectId;
    private String filename;

    public ModelDTO(ProjectModel model) {
        this.id = model.getId();
        this.name = model.getName();
        this.projectId = model.getProject().getId();
        this.filename = model.getFileName();
    }
}
