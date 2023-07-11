package ai.giskard.ml.dto;

import lombok.Getter;

@Getter
public class MLWorkerWSIdentifierSingleTestResultDTO implements MLWorkerWSBaseDTO {
    private Long id;

    private MLWorkerWSSingleTestResultDTO result;
}
