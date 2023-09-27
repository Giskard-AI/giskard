package ai.giskard.domain.ml;

import ai.giskard.domain.TestFunction;
import ai.giskard.ml.dto.MLWorkerWSGeneratedTestSuiteDTO;
import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;
import java.util.List;

@Entity
@Table(name = "suite_test")
@Getter
@Setter
@NoArgsConstructor
public class SuiteTest implements Serializable {
    @Id
    @GeneratedValue
    @Column(name = "id", nullable = false)
    private Long id;

    @ManyToOne(optional = false)
    private TestFunction testFunction;

    @Column
    private String displayName;

    @ManyToOne
    @JoinColumn(name = "test_suite")
    @NotNull
    @JsonIgnore
    private TestSuite suite;

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    @JoinColumn(name = "suite_test_id")
    private List<FunctionInput> functionInputs = new java.util.ArrayList<>();

    @OneToMany(mappedBy = "test", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private List<SuiteTestExecution> executions = new java.util.ArrayList<>();

    public SuiteTest(TestSuite suite, MLWorkerWSGeneratedTestSuiteDTO test, TestFunction testFunction) {
        this.suite = suite;
        this.testFunction = testFunction;
        this.functionInputs.addAll(test.getInputs().stream()
            .map(FunctionInput::new)
            .toList());
    }
}
