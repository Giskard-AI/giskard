package ai.giskard.domain.ml;

import ai.giskard.worker.GeneratedTestInput;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;

@Entity
@Table(name = "test_input")
@Getter
@Setter
@NoArgsConstructor
public class TestInput {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id", nullable = false)
    private Long id;

    @NotNull
    private String name;

    private String value;

    private boolean isAlias = false;

    @ManyToOne
    @JoinColumn(name = "test_id")
    @NotNull
    private SuiteTest test;

    public TestInput(SuiteTest test, GeneratedTestInput testInput) {
        this.name = testInput.getName();
        this.value = testInput.getValue();
        this.isAlias = testInput.getIsAlias();
        this.test = test;
    }
}
