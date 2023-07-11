package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSNamedSingleTestResultDTO implements MLWorkerWSBaseDTO {
    private String testUuid;

    private MLWorkerWSSingleTestResultDTO result;
}
