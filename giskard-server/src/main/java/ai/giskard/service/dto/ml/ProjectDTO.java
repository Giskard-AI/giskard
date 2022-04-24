package ai.giskard.service.dto.ml;

import ai.giskard.domain.Project;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@Getter
@Setter
@NoArgsConstructor
public class ProjectDTO {
    @Getter
    @NotNull
    private Long id;
    @Getter
    @NotNull
    private String name;
    @Getter
    private String owner;
    @Getter
    private String key;

    public ProjectDTO(Project project) {
        this.id = project.getId();
        this.name = project.getName();
        this.owner = project.getOwner().getLogin();
        this.key = project.getKey();

    }
}
