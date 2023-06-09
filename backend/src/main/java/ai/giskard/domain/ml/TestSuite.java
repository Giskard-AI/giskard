package ai.giskard.domain.ml;

import ai.giskard.domain.AbstractAuditingEntity;
import ai.giskard.domain.Project;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
import java.io.Serial;
import java.util.List;

@Entity
@Getter
@Setter
public class TestSuite extends AbstractAuditingEntity {
    @Serial
    private static final long serialVersionUID = 0L;
    @Id
    @GeneratedValue
    private Long id;

    private String name;

    @ManyToOne
    @NotNull
    private Project project;

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    @JoinColumn(name = "suite_id")
    private List<FunctionInput> functionInputs = new java.util.ArrayList<>();

    @OneToMany(mappedBy = "suite", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<SuiteTest> tests = new java.util.ArrayList<>();

    @OneToMany(mappedBy = "suite", cascade = CascadeType.ALL)
    private List<TestSuiteExecution> executions = new java.util.ArrayList<>();
}
