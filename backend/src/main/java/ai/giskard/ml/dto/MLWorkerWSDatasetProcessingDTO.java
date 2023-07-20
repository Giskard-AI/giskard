package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSDatasetProcessingDTO implements MLWorkerWSBaseDTO {
    private String datasetId;

    private Integer totalRows;

    private List<Integer> filteredRows;

    private List<MLWorkerWSDatasetRowModificationResultDTO> modifications;
}
