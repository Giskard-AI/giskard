package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.List;

@Getter
public class MLWorkerWSRunAdHocTestDTO implements MLWorkerWSBaseDTO {
    private List<MLWorkerWSNamedSingleTestResultDTO> results;
}
