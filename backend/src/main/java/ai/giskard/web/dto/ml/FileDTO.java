package ai.giskard.web.dto.ml;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.time.Instant;

@Getter
@Setter
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

    private long size;

    public String getName() {
        return name != null ? name : fileName;
    }

    public Long getProjectId() {
        return project == null ? null : project.getId();
    }

}
