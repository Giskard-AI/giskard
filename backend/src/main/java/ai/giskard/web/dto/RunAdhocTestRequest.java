package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Map;
import java.util.UUID;

@Getter
@AllArgsConstructor
@NoArgsConstructor
@UIModel
public class RunAdhocTestRequest {
    private Long projectId;
    private UUID testUuid;
    private Map<String, Object> inputs;
}
