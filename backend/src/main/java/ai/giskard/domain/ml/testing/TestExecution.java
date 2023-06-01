package ai.giskard.domain.ml.testing;

import ai.giskard.domain.BaseEntity;
import ai.giskard.domain.ml.TestResult;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.Entity;
import javax.persistence.EnumType;
import javax.persistence.Enumerated;
import javax.persistence.ManyToOne;
import java.util.Date;

@Entity
@NoArgsConstructor
@Getter
@Setter
public class TestExecution extends BaseEntity {
    @ManyToOne
    Test test;

    Date executionDate = new Date();

    @Enumerated(EnumType.STRING)
    TestResult result;

    public TestExecution(Test test) {
        this.test = test;
    }
}
