package ai.giskard.ml.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@Setter
@Getter
public class MLWorkerWSDataRowDTO implements MLWorkerWSBaseDTO {
    Map<String, String> columns;
}
