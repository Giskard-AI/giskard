package ai.giskard.domain.ml;

import ai.giskard.domain.BaseEntity;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@Entity
@NoArgsConstructor
@Getter
@Setter
public class TestSuiteExecution extends BaseEntity {


    @ManyToOne
    @JsonIgnore
    private TestSuite suite;

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    @JoinColumn(name = "test_suite_execution_id")
    private List<FunctionInput> inputs;

    @Enumerated(EnumType.STRING)
    private TestResult result;

    private String message;

    @Column(columnDefinition = "VARCHAR")
    private String logs;

    @OneToMany(mappedBy = "execution", cascade = CascadeType.ALL)
    private List<SuiteTestExecution> results = new ArrayList<>();

    private Date executionDate = new Date();
    private Date completionDate;

    public TestSuiteExecution(TestSuite suite) {
        this.suite = suite;
    }
}
