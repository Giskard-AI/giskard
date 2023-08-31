package ai.giskard.ml.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class MLWorkerWSDatasetProcessingParamDTO implements MLWorkerWSBaseDTO {
    private MLWorkerWSArtifactRefDTO dataset;

    private List<MLWorkerWSDatasetProcessingFunctionDTO> functions;
}
