package ai.giskard.domain.ml;


import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import java.nio.file.Path;
import java.nio.file.Paths;

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

    private String location;

    private String target;

    public Path getPredictionsPath() {
        return Paths.get(location, "predictions.csv");
    }

    public Path getCalculatedPath() {
        return Paths.get(location, "calculated.csv");
    }
}
