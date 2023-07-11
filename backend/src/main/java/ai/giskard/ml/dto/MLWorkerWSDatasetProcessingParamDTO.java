package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSDatasetProcessingParamDTO implements MLWorkerWSBaseDTO {
    MLWorkerWSArtifactRefDTO dataset;

    List<MLWorkerWSDatasetProcessingFunctionDTO> functions;
}
