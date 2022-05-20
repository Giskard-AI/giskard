package ai.giskard.domain.ml;


import ai.giskard.domain.ProjectFile;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.HashSet;
import java.util.Set;

@Entity(name = "datasets")
@NoArgsConstructor
@Getter
public class Dataset extends ProjectFile {
    @Setter
    private String name;

    @Column(columnDefinition = "VARCHAR")
    @Setter
    private String featureTypes;
    @Setter
    private String target;

    @Setter
    @OneToMany(mappedBy = "dataset", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Inspection> inspections = new HashSet<>();

}
