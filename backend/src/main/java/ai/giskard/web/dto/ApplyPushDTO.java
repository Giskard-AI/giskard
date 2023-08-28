package ai.giskard.web.dto;

//import ai.giskard.worker.CallToActionKind;
//import ai.giskard.worker.PushKind;

import ai.giskard.domain.ml.CallToActionKind;
import ai.giskard.domain.ml.PushKind;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;
import java.util.UUID;

@Getter
@Setter
@UIModel
@NoArgsConstructor
public class ApplyPushDTO {
    private UUID modelId;
    private UUID datasetId;
    private int rowIdx;
    private PushKind pushKind;
    private CallToActionKind ctaKind;
    private Map<String, String> features;
}
