package ai.giskard.domain.ml;

import ai.giskard.domain.TestFunction;
import ai.giskard.ml.dto.MLWorkerWSGeneratedTestSuiteDTO;
import ai.giskard.worker.GeneratedTest;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
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

    public SuiteTest(TestSuite suite, GeneratedTest test, TestFunction testFunction) {
        this.suite = suite;
        this.testFunction = testFunction;
        this.functionInputs.addAll(test.getInputsList().stream()
            .map(FunctionInput::new)
            .toList());
    }

    public SuiteTest(TestSuite suite, MLWorkerWSGeneratedTestSuiteDTO test, TestFunction testFunction) {
        this.suite = suite;
        this.testFunction = testFunction;
        this.functionInputs.addAll(test.getInputs().stream()
            .map(FunctionInput::new)
            .toList());
    }
}
