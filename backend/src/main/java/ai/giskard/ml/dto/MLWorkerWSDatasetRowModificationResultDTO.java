package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.Map;

@Getter
public class MLWorkerWSDatasetRowModificationResultDTO implements MLWorkerWSBaseDTO {
    Integer rowId;

    Map<String, String> modifications;
}
