package ai.giskard.web.dto;

import lombok.Data;

import java.util.Map;

@Data
public class TransformationResultMessageDTO {
    private int rowId;
    private Map<String, String> modifications;
}
