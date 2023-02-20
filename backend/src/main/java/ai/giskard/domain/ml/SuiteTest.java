package ai.giskard.domain.ml;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;
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

    private String testId;

    @ManyToOne
    @JoinColumn(name = "test_suite")
    @NotNull
    private TestSuiteNew suite;

    @OneToMany(mappedBy = "test", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<TestInput> testInputs = new java.util.ArrayList<>();

    @OneToMany(mappedBy = "test", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @JsonIgnore
    private List<SuiteTestExecution> executions = new java.util.ArrayList<>();
}
