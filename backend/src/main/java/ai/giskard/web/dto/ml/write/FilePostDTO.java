package ai.giskard.web.dto.ml.write;

import ai.giskard.web.dto.ml.ProjectDTO;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
public abstract class FilePostDTO {
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

}
