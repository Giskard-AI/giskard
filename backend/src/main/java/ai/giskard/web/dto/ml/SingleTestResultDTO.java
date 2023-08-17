package ai.giskard.web.dto.ml;

import ai.giskard.ml.dto.MLWorkerWSSingleTestResultDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class SingleTestResultDTO {
    private List<TestResultMessageDTO> messages;
    private List<Integer> actualSlicesSize;
    private List<Integer> referenceSlicesSize;
    private boolean passed;
    private List<Integer> partialUnexpectedIndexList;
    private List<Integer> unexpectedIndexList;
    private Integer missingCount;
    private Double missingPercent;
    private Integer unexpectedCount;
    private Double unexpectedPercent;
    private Double unexpectedPercentTotal;
    private Double unexpectedPercentNonmissing;
    private float metric;
    private String outputDfUuid;


    public SingleTestResultDTO(MLWorkerWSSingleTestResultDTO message) {
        this.missingCount = message.getMissingCount();
        this.missingPercent = message.getMissingPercent();
        this.unexpectedCount = message.getUnexpectedCount();
        this.unexpectedPercent = message.getUnexpectedPercent();
        this.unexpectedPercentTotal = message.getUnexpectedPercentTotal();
        this.unexpectedPercentNonmissing = message.getUnexpectedPercentNonmissing();
        this.partialUnexpectedIndexList = message.getPartialUnexpectedIndexList();
        this.unexpectedIndexList = message.getUnexpectedIndexList();
        this.passed = message.getPassed();
        this.metric = message.getMetric();
        this.actualSlicesSize = message.getActualSlicesSize();
        this.referenceSlicesSize = message.getReferenceSlicesSize();
        this.messages = message.getMessages().stream().map(
            msg -> new TestResultMessageDTO(msg.getType(), msg.getText())).toList();
        this.outputDfUuid = message.getOutputDfId();
    }
}
