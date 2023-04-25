package ai.giskard.web.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class RequiredInputDTO {
    private String type;
    private boolean sharedInput;
}
