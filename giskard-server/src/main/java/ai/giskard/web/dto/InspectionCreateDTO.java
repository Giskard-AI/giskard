package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@UIModel
public class InspectionCreateDTO {
    private Long modelId;
    private Long datasetId;
}
