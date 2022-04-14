package ai.giskard.service.dto.ml;

import ai.giskard.worker.SingleTestResult;
import ai.giskard.worker.TestResultMessage;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
public class SingleTestResultDTO {
    private boolean passed;
    private List<Integer> partialUnexpectedIndexList;
    //private List<TestResultMessage.Partial_unexpected_counts> partialUnexpectedCounts;
    private List<Integer> unexpectedIndexList;
    private int missingCount;
    private double missingPercent;
    private int unexpectedCount;
    private double unexpectedPercent;
    private double unexpectedPercentTotal;
    private double unexpectedPercentNonmissing;
    private int elementCount;

    public SingleTestResultDTO(SingleTestResult message) {
        this.elementCount = message.getElementCount();
        this.missingCount = message.getMissingCount();
        this.missingPercent = message.getMissingPercent();
        this.unexpectedCount = message.getUnexpectedCount();
        this.unexpectedPercent = message.getUnexpectedPercent();
        this.unexpectedPercentTotal = message.getUnexpectedPercentTotal();
        this.unexpectedPercentNonmissing = message.getUnexpectedPercentNonmissing();
        this.partialUnexpectedIndexList = message.getPartialUnexpectedIndexListList();
        //this.partialUnexpectedCounts = message.getPartialUnexpectedCountsList();
        this.unexpectedIndexList = message.getUnexpectedIndexListList();
        this.passed = message.getPassed();
    }
}
