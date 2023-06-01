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
@Getter
@Setter
public class TestSuiteNew extends AbstractAuditingEntity {
    @Id
    //@GeneratedValue(strategy = GenerationType.UUID)
    private String id;
    @NotNull
    private String name;

    @ManyToOne
    @NotNull
    private Project project;

    @ManyToOne
    private Dataset referenceDataset;

    @ManyToOne
    private Dataset actualDataset;

    @ManyToOne
    private ProjectModel model;

    @OneToMany(mappedBy = "testSuite", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private Set<Test> tests = new HashSet<>();
}
