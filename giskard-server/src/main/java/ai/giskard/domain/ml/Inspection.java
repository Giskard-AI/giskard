package ai.giskard.domain.ml;


import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Getter
@Setter
@Entity(name = "inspections")
public class Inspection {
    @Getter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @ManyToOne
    private Dataset dataset;

    @ManyToOne
    private ProjectModel model;


}
