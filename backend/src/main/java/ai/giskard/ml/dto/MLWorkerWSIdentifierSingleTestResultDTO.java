package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSIdentifierSingleTestResultDTO implements MLWorkerWSBaseDTO {
    private Long id;

    private MLWorkerWSSingleTestResultDTO result;

    private List<MLWorkerWSFuncArgumentDTO> arguments;
}
