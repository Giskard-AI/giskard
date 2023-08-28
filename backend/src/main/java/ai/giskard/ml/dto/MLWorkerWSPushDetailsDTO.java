package ai.giskard.ml.dto;

import ai.giskard.domain.ml.CallToActionKind;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MLWorkerWSPushDetailsDTO implements MLWorkerWSBaseDTO {
    public String action;
    public String explanation;
    public String button;
    public CallToActionKind cta;
}
