package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
public class MLWorkerWSExplainParamDTO implements MLWorkerWSBaseDTO {
    private MLWorkerWSArtifactRefDTO model;

    private MLWorkerWSArtifactRefDTO dataset;

    private Map<String, String> columns;
}
