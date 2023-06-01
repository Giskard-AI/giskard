package ai.giskard.web.dto;

import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@AllArgsConstructor
@UIModel
public class TestSuiteCompleteDTO {
    private TestSuiteNewDTO suite;
    private List<TestFunctionDTO> registry;
    private List<DatasetDTO> datasets;
    private List<ModelDTO> models;
    private List<TestSuiteExecutionDTO> executions;
    private Map<String, String> inputs;

}
