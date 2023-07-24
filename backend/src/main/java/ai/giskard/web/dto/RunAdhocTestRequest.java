package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

@Getter
@AllArgsConstructor
@NoArgsConstructor
@UIModel
public class RunAdhocTestRequest {
    private Long projectId;
    private String testUuid;
    private List<FunctionInputDTO> inputs;
    private boolean debug;
}
