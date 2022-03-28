package ai.giskard.domain.ml;

import ai.giskard.domain.ProjectFile;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.NonNull;
import lombok.Setter;

import javax.persistence.Entity;

@Entity(name = "project_models")
@NoArgsConstructor
public class ProjectModel extends ProjectFile {
    @NonNull
    private String pythonVersion;
    @NonNull
    private String requirementsFileLocation;
    @Getter
    @Setter
    private String name;
}
