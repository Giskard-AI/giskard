package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class MLWorkerWSDataFrameDTO implements MLWorkerWSBaseDTO {
    private List<MLWorkerWSDataRowDTO> rows;
}
