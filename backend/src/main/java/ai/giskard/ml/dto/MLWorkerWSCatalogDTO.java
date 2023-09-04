package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.Map;

@Getter
public class MLWorkerWSCatalogDTO implements MLWorkerWSBaseDTO {
    private Map<String, MLWorkerWSFunctionMetaDTO> tests;

    private Map<String, MLWorkerWSDatasetProcessFunctionMetaDTO> slices;

    private Map<String, MLWorkerWSDatasetProcessFunctionMetaDTO> transformations;
}
