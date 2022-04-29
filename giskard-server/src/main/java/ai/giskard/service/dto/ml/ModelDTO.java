package ai.giskard.service.dto.ml;

import ai.giskard.domain.ml.ProjectModel;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;

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
