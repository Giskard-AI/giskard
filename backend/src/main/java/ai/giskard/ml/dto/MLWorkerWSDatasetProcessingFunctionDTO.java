package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.jackson.Jacksonized;

import java.util.List;

@Getter
@Setter
@Builder
@Jacksonized
public class MLWorkerWSDatasetProcessingFunctionDTO implements MLWorkerWSBaseDTO {
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO slicingFunction;

    @JsonInclude(JsonInclude.Include.NON_NULL)
    private MLWorkerWSArtifactRefDTO transformationFunction;

    private List<MLWorkerWSFuncArgumentDTO> arguments;
}
