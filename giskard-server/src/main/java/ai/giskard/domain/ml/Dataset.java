package ai.giskard.domain.ml;


import ai.giskard.domain.ProjectFile;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.CascadeType;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.OneToMany;
import java.util.HashSet;
import java.util.Set;

@Entity(name = "datasets")
@NoArgsConstructor
public class Dataset extends ProjectFile {
    @Getter
    @Setter
    private String name;

//    @Getter
//    @Setter
//    private String inputTypes;

    @Getter
    @Setter
    @OneToMany(mappedBy = "dataset", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Inspection> inspections = new HashSet<>();

}
