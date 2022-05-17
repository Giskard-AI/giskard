package ai.giskard.domain.ml;

import ai.giskard.domain.ProjectFile;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.NonNull;
import lombok.Setter;

import javax.persistence.CascadeType;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.OneToMany;
import java.io.Serializable;
import java.util.HashSet;
import java.util.Set;


@Entity(name = "project_models")
@NoArgsConstructor
public class ProjectModel extends ProjectFile implements Serializable {
    @Getter
    @Setter
    @NonNull
    private String pythonVersion;
    @NonNull
    private String requirementsFileLocation;
    @Getter
    @Setter
    private String name;

    @Getter
    @Setter
    @OneToMany(mappedBy = "model", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Inspection> inspections = new HashSet<>();
}
