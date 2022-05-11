package ai.giskard.domain.ml;

import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.Project;
import ai.giskard.domain.ml.testing.Test;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.util.HashSet;
import java.util.Set;

@Entity
public class TestSuite extends AbstractAuditingEntity {
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

    @Getter
    @Setter
    @OneToMany(mappedBy = "testSuite", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Test> tests = new HashSet<>();
}
