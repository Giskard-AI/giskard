package ai.giskard.web.dto.ml;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
public abstract class FileDTO {
    @JsonProperty("id")
    @NotNull
    protected Long id;

    @JsonIgnore
    protected ProjectDTO project;

    @JsonProperty("file_name")
    protected String fileName;

    private String name;

    @JsonProperty("creation_date")
    protected LocalDateTime createdOn;

    protected String location;

    public String getName() {
        return name != null ? name : fileName;
    }

    public Long getSize() throws IOException {
        return (location != null && Files.exists(Paths.get(location))) ? Files.size(Paths.get(location)) : 0L;
    }

    public Long getProjectId() {
        return project.getId();
    }

}
