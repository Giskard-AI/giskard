package ai.giskard.service.dto.ml;


import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;
@UIModel
public class ExecuteTestSuiteRequest {
    @Setter @Getter
    Long suiteId;
}
