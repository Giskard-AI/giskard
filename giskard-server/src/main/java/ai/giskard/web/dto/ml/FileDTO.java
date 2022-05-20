package ai.giskard.web.dto.ml;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.LocalDateTime;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public abstract class FileDTO {
    @JsonProperty("id")
    @NotNull
    protected Long id;

    @JsonIgnore
    protected ProjectDTO project;

    protected String fileName;

    private String name;

    protected Instant createdDate;

    protected String location;

    public String getName() {
        return name != null ? name : fileName;
    }

    public Long getSize() throws IOException {
        return (location != null && Files.exists(Paths.get(location))) ? Files.size(Paths.get(location)) : 0L;
    }

    public Long getProjectId() {
        return project == null ? null : project.getId();
    }

}
