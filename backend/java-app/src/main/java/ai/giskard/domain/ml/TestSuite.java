package ai.giskard.domain.ml;

import ai.giskard.domain.Project;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;

@Entity
public class TestSuite {
    @lombok.Setter
    @lombok.Getter
    @Id
    @NotNull
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id", nullable = false)
    private Long id;

    @Getter
    @Setter
    @NotNull
    private String name;

    @Getter
    @Setter
    @ManyToOne
    @NotNull
    private Project project;

    @Getter
    @Setter
    @ManyToOne
    private Dataset trainDataset;

    @Getter
    @Setter
    @ManyToOne
    private Dataset testDataset;

    @Getter
    @Setter
    @ManyToOne
    private ProjectModel model;


}
