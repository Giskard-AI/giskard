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
    private TestSuiteNew suite;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, String> inputs;

    @Enumerated(EnumType.STRING)
    private TestResult result;

    @OneToMany(mappedBy = "execution", cascade = CascadeType.ALL)
    private List<SuiteTestExecution> results = new ArrayList<>();

    private Date executionDate = new Date();
    private Date completionDate;

    public TestSuiteExecution(TestSuiteNew suite) {
        this.suite = suite;
    }
}
