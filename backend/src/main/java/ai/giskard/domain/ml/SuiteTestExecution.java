package ai.giskard.domain.ml;

import ai.giskard.domain.BaseEntity;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.ml.TestResultMessageDTO;
import ai.giskard.worker.FuncArgument;
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
    private Map<String, String> arguments;

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
                              SingleTestResult message,
                              List<FuncArgument> arguments) {
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
        this.passed = message.getPassed();
        this.metric = message.getMetric();
        this.actualSlicesSize = message.getActualSlicesSizeList();
        this.referenceSlicesSize = message.getReferenceSlicesSizeList();
        this.messages = message.getMessagesList().stream().map(
            msg -> new TestResultMessageDTO(msg.getType(), msg.getText())).toList();
        this.inputs = test.getFunctionInputs().stream()
            .collect(Collectors.toMap(FunctionInput::getName, FunctionInput::getValue));
        this.arguments = arguments.stream()
            .collect(Collectors.toMap(FuncArgument::getName, this::getFuncArgValue));
    }

    private String getFuncArgValue(FuncArgument funcArgument) {
        String result = "";
        switch (funcArgument.getArgumentCase()) {
            case MODEL:
                result = funcArgument.getModel().getId();
                break;
            case DATASET:
                result = funcArgument.getDataset().getId();
                break;
            case SLICINGFUNCTION:
                // Not sure how to handle this cleanly yet.
                break;
            case TRANSFORMATIONFUNCTION:
                // Not sure how to handle this cleanly yet.
                break;
            case KWARGS:
                // Not sure how to handle this cleanly yet.
                break;
            case ARGUMENT_NOT_SET:
                break;
            case BOOL:
                result = String.valueOf(funcArgument.getBool());
                break;
            case FLOAT:
                result = String.valueOf(funcArgument.getFloat());
                break;
            case INT:
                result = String.valueOf(funcArgument.getInt());
                break;
            case STR:
                result = funcArgument.getStr();
                break;
        }

        return result;
    }
}
