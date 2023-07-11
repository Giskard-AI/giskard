package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSTestSuiteParamDTO implements MLWorkerWSBaseDTO {
    List<MLWorkerWSSuiteTestArgumentDTO> tests;

    List<MLWorkerWSFuncArgumentDTO> globalArguments;
}
