package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSDatasetProcessingDTO implements MLWorkerWSBaseDTO {
    String datasetId;

    Integer totalRows;

    List<Integer> filteredRows;

    List<MLWorkerWSDatasetRowModificationResultDTO> modifications;
}
