package ai.giskard.domain.ml;


import ai.giskard.domain.ProjectFile;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.Entity;

@Entity(name = "datasets")
@NoArgsConstructor
public class Dataset extends ProjectFile {
    @Getter
    @Setter
    private String name;
}
