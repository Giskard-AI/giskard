package ai.giskard.domain.ml;

import ai.giskard.domain.BaseEntity;
import ai.giskard.utils.GRPCUtils;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.ml.TestResultMessageDTO;
import ai.giskard.worker.SingleTestResult;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.Column;
import javax.persistence.Convert;
import javax.persistence.Entity;
import javax.persistence.ManyToOne;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Entity
@NoArgsConstructor
@Getter
@Setter
public class SuiteTestExecution extends BaseEntity {

    @ManyToOne(optional = false)
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

    private boolean passed;

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
        this.missingCount = GRPCUtils.convertType(message.getMissingCount());
        this.missingPercent = GRPCUtils.convertType(message.getMissingPercent());
        this.unexpectedCount = GRPCUtils.convertType(message.getUnexpectedCount());
        this.unexpectedPercent = GRPCUtils.convertType(message.getUnexpectedPercent());
        this.unexpectedPercentTotal = GRPCUtils.convertType(message.getUnexpectedPercentTotal());
        this.unexpectedPercentNonmissing = GRPCUtils.convertType(message.getUnexpectedPercentNonmissing());
        this.partialUnexpectedIndexList = message.getPartialUnexpectedIndexListList();
        this.unexpectedIndexList = message.getUnexpectedIndexListList();
        this.passed = message.getPassed();
        this.metric = message.getMetric();
        this.actualSlicesSize = message.getActualSlicesSizeList();
        this.referenceSlicesSize = message.getReferenceSlicesSizeList();
        this.messages = message.getMessagesList().stream().map(
            msg -> new TestResultMessageDTO(msg.getType(), msg.getText())).toList();
        this.inputs = test.getTestInputs().stream()
            .collect(Collectors.toMap(TestInput::getName, TestInput::getValue));
    }

}
