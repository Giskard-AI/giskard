package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class InspectionCreateDTO {
    private String name;
    private UUID modelId;
    private UUID datasetId;
    private boolean sample;
}
