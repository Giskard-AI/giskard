package ai.giskard.ml.dto;

import lombok.Getter;

@Getter
public class MLWorkerWSNamedSingleTestResultDTO implements MLWorkerWSBaseDTO {
    private String testUuid;

    private MLWorkerWSSingleTestResultDTO result;
}
