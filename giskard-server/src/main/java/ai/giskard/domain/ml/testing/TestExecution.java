package ai.giskard.domain.ml.testing;

import ai.giskard.domain.ml.TestResult;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.Date;

@Entity
@NoArgsConstructor
public class TestExecution {
    @Setter
    @Getter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Getter
    @Setter
    @ManyToOne
    Test test;

    @Getter
    @Setter
    Date executionDate = new Date();

    @Getter
    @Setter
    @Enumerated(EnumType.STRING)
    TestResult result;

    public TestExecution(Test test) {
        this.test = test;
    }
}
