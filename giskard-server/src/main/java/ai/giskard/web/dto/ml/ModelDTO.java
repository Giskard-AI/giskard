package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.ProjectModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ModelDTO extends FileDTO {

    @JsonProperty("python_version")
    private String pythonVersion;

    public ModelDTO(ProjectModel model) {
        this.id = model.getId();
        this.fileName = model.getFileName();
        this.pythonVersion = model.getPythonVersion();
    }

}
