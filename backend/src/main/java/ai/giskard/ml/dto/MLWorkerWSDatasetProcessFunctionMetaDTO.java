package ai.giskard.ml.dto;

import lombok.Getter;

@Getter
public class MLWorkerWSDatasetProcessFunctionMetaDTO extends MLWorkerWSFunctionMetaDTO {
    private Boolean cellLevel;

    private String columnType;

    private String processType;
}
