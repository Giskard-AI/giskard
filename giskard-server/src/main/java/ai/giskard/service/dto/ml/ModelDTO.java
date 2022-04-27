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
public class ModelDTO {
    @JsonProperty("id")
    @NotNull
    protected Long id;
    @JsonIgnore
    protected ProjectDTO project;
    @JsonProperty("name")
    protected String fileName;
    @JsonProperty("python_version")
    private String pythonVersion;
    @JsonProperty("creation_date")
    protected LocalDateTime createdOn;
    protected String location;

    public Long getSize() throws IOException {
        Path path = Paths.get(location);
        if (Files.exists(path)) {
            return Files.size(path);
        } else {
            return 0L;
        }
    }

    public Long getProjectId() {
        return project.getId();
    }

    public ModelDTO(ProjectModel model) {
        this.id = model.getId();
        this.fileName = model.getFileName();
        this.pythonVersion = model.getPythonVersion();
    }

}
