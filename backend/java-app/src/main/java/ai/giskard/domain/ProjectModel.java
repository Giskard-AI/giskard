package ai.giskard.domain;

import lombok.NoArgsConstructor;
import lombok.NonNull;

import javax.persistence.Entity;

@Entity
@NoArgsConstructor
public class ProjectModel extends ProjectFile {
    @NonNull
    private String pythonVersion;
    @NonNull
    private String requirementsFileLocation;
}
