package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Getter
@Setter
@UIModel
@NoArgsConstructor
public class ApplyPushDTO {
    private UUID modelId;
    private UUID datasetId;
    private int rowIdx;
    private int kind;
    private int pushIdx;
}
