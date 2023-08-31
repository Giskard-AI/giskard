package ai.giskard.ml.dto;

import ai.giskard.domain.ml.CallToActionKind;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSPushDetailsDTO implements MLWorkerWSBaseDTO {
    private String action;
    private String explanation;
    private String button;
    private CallToActionKind cta;
}
