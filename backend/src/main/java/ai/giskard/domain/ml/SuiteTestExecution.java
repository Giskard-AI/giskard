package ai.giskard.domain.ml;

import ai.giskard.domain.BaseEntity;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.ml.TestResultMessageDTO;
import ai.giskard.worker.SingleTestResult;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Entity
@NoArgsConstructor
@Getter
@Setter
public class SuiteTestExecution extends BaseEntity {

    private Long id;

    @ManyToOne(optional = false)
    @JsonIgnore
    private SuiteTest test;

    @ManyToOne
    @JsonIgnore
    private TestSuiteExecution execution;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, String> inputs;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<TestResultMessageDTO> messages;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<Integer> actualSlicesSize;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<Integer> referenceSlicesSize;

    @Enumerated(EnumType.STRING)
    private TestResult status;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<Integer> partialUnexpectedIndexList;

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<Integer> unexpectedIndexList;

    private Integer missingCount;

    private Double missingPercent;

    private Integer unexpectedCount;

    private Double unexpectedPercent;

    private Double unexpectedPercentTotal;

    private Double unexpectedPercentNonmissing;

    @Column(nullable = false)
    private float metric;

    public SuiteTestExecution(SuiteTest test,
                              TestSuiteExecution execution,
                              SingleTestResult message) {
        this.test = test;
        this.execution = execution;
        this.missingCount = message.getMissingCount();
        this.missingPercent = message.getMissingPercent();
        this.unexpectedCount = message.getUnexpectedCount();
        this.unexpectedPercent = message.getUnexpectedPercent();
        this.unexpectedPercentTotal = message.getUnexpectedPercentTotal();
        this.unexpectedPercentNonmissing = message.getUnexpectedPercentNonmissing();
        this.partialUnexpectedIndexList = message.getPartialUnexpectedIndexListList();
        this.unexpectedIndexList = message.getUnexpectedIndexListList();
        this.status = message.getIsError()
            ? TestResult.ERROR : message.getPassed()
            ? TestResult.PASSED : TestResult.ERROR;
        this.metric = message.getMetric();
        this.actualSlicesSize = message.getActualSlicesSizeList();
        this.referenceSlicesSize = message.getReferenceSlicesSizeList();
        this.messages = message.getMessagesList().stream().map(
            msg -> new TestResultMessageDTO(msg.getType(), msg.getText())).toList();
        this.inputs = test.getFunctionInputs().stream()
            .collect(Collectors.toMap(FunctionInput::getName, FunctionInput::getValue));
    }

}
