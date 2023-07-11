package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSRunAdHocTestParamDTO implements MLWorkerWSBaseDTO {
    private String testUuid;

    private List<MLWorkerWSFuncArgumentDTO> arguments;
}
