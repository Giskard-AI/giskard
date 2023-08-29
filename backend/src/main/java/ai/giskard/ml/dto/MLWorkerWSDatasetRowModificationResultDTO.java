package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.Map;

@Getter
public class MLWorkerWSDatasetRowModificationResultDTO implements MLWorkerWSBaseDTO {
    private Integer rowId;

    private Map<String, String> modifications;
}
