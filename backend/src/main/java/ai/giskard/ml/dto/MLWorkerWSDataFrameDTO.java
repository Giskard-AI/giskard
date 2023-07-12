package ai.giskard.ml.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.jackson.Jacksonized;

import java.util.List;

@Getter
@Setter
@Builder
@Jacksonized
public class MLWorkerWSDataFrameDTO implements MLWorkerWSBaseDTO {
    private List<MLWorkerWSDataRowDTO> rows;
}
