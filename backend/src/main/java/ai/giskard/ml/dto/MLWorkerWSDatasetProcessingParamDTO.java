package ai.giskard.ml.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class MLWorkerWSDatasetProcessingParamDTO implements MLWorkerWSBaseDTO {
    MLWorkerWSArtifactRefDTO dataset;

    List<MLWorkerWSDatasetProcessingFunctionDTO> functions;
}
