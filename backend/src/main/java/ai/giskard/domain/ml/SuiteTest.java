package ai.giskard.domain.ml;

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

    @OneToMany(mappedBy = "test", cascade = CascadeType.ALL)
    private List<TestInput> testInputs = new java.util.ArrayList<>();

}
