package ai.giskard.domain.ml;

import ai.giskard.domain.BaseEntity;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

@Entity
@NoArgsConstructor
@Getter
@Setter
public class TestSuiteExecution extends BaseEntity {


    @ManyToOne
    TestSuiteNew suite;

    Date executionDate = new Date();

    Date completionDate;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, String> inputs;

    @Enumerated(EnumType.STRING)
    TestResult result;

    @OneToMany(mappedBy = "execution", cascade = CascadeType.ALL)
    private List<SuiteTestExecution> results = new ArrayList<>();

    // TODO: add status for job in progress

    public TestSuiteExecution(TestSuiteNew suite) {
        this.suite = suite;
    }
}
