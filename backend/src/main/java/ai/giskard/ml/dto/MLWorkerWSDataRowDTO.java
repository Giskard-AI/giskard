package ai.giskard.ml.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.jackson.Jacksonized;

import java.util.Map;

@Setter
@Getter
@Builder
@Jacksonized
public class MLWorkerWSDataRowDTO implements MLWorkerWSBaseDTO {
    Map<String, String> columns;
}
