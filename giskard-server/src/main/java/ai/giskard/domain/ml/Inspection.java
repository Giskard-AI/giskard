package ai.giskard.domain.ml;


import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Entity(name = "inspections")
public class Inspection {
    @Getter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Getter
    @Setter
    @ManyToOne
    private Dataset dataset;

    @Getter
    @Setter
    @ManyToOne
    private ProjectModel model;

    @Getter
    @Setter
    private String location;

    @Getter
    @Setter
    private String target;

}
