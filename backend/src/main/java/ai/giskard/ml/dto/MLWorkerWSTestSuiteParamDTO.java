package ai.giskard.ml.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class MLWorkerWSTestSuiteParamDTO implements MLWorkerWSBaseDTO {
    private List<MLWorkerWSSuiteTestArgumentDTO> tests;

    private List<MLWorkerWSFuncArgumentDTO> globalArguments;
}
