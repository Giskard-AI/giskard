package ai.giskard.domain.ml;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import javax.validation.constraints.NotNull;

@Entity
@Table(name = "test_parameter")
@Getter
@Setter
@NoArgsConstructor
public class TestParameter {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(name = "id", nullable = false)
    private Long id;

    @NotNull
    private String name;

    private String value;

    @ManyToOne
    @JoinColumn(name = "test_id")
    @NotNull
    private SuiteTest test;

    public TestParameter(String name, String value, SuiteTest test) {
        this.name = name;
        this.value = value;
        this.test = test;
    }
}
