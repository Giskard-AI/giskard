package ai.giskard.domain.ml;

import ai.giskard.domain.BaseEntity;
import ai.giskard.ml.dto.MLWorkerWSFuncArgumentDTO;
import ai.giskard.ml.dto.MLWorkerWSSingleTestResultDTO;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.ml.TestResultMessageDTO;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.HashMap;
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
                              MLWorkerWSSingleTestResultDTO message,
                              List<MLWorkerWSFuncArgumentDTO> arguments) {
        this.test = test;
        this.execution = execution;
        this.missingCount = message.getMissingCount();
        this.missingPercent = message.getMissingPercent();
        this.unexpectedCount = message.getUnexpectedCount();
        this.unexpectedPercent = message.getUnexpectedPercent();
        this.unexpectedPercentTotal = message.getUnexpectedPercentTotal();
        this.unexpectedPercentNonmissing = message.getUnexpectedPercentNonmissing();
        this.partialUnexpectedIndexList = message.getPartialUnexpectedIndexList();
        this.unexpectedIndexList = message.getUnexpectedIndexList();
        if (Boolean.TRUE.equals(message.getIsError())) {
            this.status = TestResult.ERROR;
        } else {
            this.status = Boolean.TRUE.equals(message.getPassed()) ? TestResult.PASSED : TestResult.FAILED;
        }
        this.metric = message.getMetric();
        this.actualSlicesSize = message.getActualSlicesSize();
        this.referenceSlicesSize = message.getReferenceSlicesSize();
        this.messages = message.getMessages().stream().map(
            msg -> new TestResultMessageDTO(msg.getType(), msg.getText())).toList();
        this.inputs = test.getFunctionInputs().stream()
            .collect(Collectors.toMap(FunctionInput::getName, FunctionInput::getValue));
        this.arguments = arguments.stream()
            .collect(Collectors.toMap(MLWorkerWSFuncArgumentDTO::getName, this::getFuncArgValueWS));
    }

    private String getFuncArgValueWS(MLWorkerWSFuncArgumentDTO funcArgument) {
        String result = "";
        if (funcArgument.getModel() != null) {
            result = funcArgument.getModel().getId();
        } else if (funcArgument.getDataset() != null) {
            result = funcArgument.getDataset().getId();
        } else if (funcArgument.getSlicingFunction() != null) {
            result = funcArgument.getSlicingFunction().getId();
        } else if (funcArgument.getTransformationFunction() != null) {
            result = funcArgument.getTransformationFunction().getId();
        } else if (funcArgument.getBoolValue() != null) {
            result = String.valueOf(funcArgument.getBoolValue());
        } else if (funcArgument.getFloatValue() != null) {
            result = String.valueOf(funcArgument.getFloatValue());
        } else if (funcArgument.getIntValue() != null) {
            result = String.valueOf(funcArgument.getIntValue());
        } else if (funcArgument.getStrValue() != null) {
            result = funcArgument.getStrValue();
        }

        Map<String, String> args = funcArgument.getArgs() == null ? new HashMap<>() : funcArgument.getArgs().stream()
            .collect(Collectors.toMap(MLWorkerWSFuncArgumentDTO::getName, this::getFuncArgValueWS));

        Map<String, Object> json = Map.of(
            "value", result,
            "args", args
        );

        // return json as a json
        return new ObjectMapper().valueToTree(json).toString();
    }
}
