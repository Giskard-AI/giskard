package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSSuiteTestArgumentDTO implements MLWorkerWSBaseDTO {
    private Long id;

    private String testUuid;

    private List<MLWorkerWSFuncArgumentDTO> arguments;
}
