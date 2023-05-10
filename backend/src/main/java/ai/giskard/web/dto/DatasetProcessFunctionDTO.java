package ai.giskard.web.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@Data
@EqualsAndHashCode(callSuper = true)
@AllArgsConstructor
@NoArgsConstructor
public class DatasetProcessFunctionDTO extends CallableDTO {
    private boolean cellLevel;
    private String columnType;
}
