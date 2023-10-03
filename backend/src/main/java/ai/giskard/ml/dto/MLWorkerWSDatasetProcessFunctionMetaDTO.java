package ai.giskard.ml.dto;

import lombok.Getter;

@Getter
public class MLWorkerWSDatasetProcessFunctionMetaDTO extends MLWorkerWSFunctionMetaBaseDTO {
    private Boolean cellLevel;

    private String columnType;

    private String processType;
}
