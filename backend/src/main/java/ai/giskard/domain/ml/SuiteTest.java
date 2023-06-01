package ai.giskard.domain.ml;

import ai.giskard.domain.TestFunction;
import ai.giskard.worker.GeneratedTest;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.List;

@Entity
@Table(name = "suite_test")
@Getter
@Setter
@NoArgsConstructor
public class SuiteTest {
    @Id
    @GeneratedValue
    @Column(name = "id", nullable = false)
    private Long id;

    @ManyToOne(optional = false)
    private TestFunction testFunction;

    @ManyToOne
    @JoinColumn(name = "test_suite")
    private TestSuiteNew suite;

    @OneToMany(mappedBy = "test", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<TestInput> testInputs = new java.util.ArrayList<>();

    @OneToMany(mappedBy = "test", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private List<SuiteTestExecution> executions = new java.util.ArrayList<>();

    public SuiteTest(TestSuiteNew suite, GeneratedTest test, TestFunction testFunction) {
        this.suite = suite;
        this.testFunction = testFunction;
        this.testInputs.addAll(test.getInputsList().stream()
            .map(testInput -> new TestInput(this, testInput))
            .toList());
    }
}
