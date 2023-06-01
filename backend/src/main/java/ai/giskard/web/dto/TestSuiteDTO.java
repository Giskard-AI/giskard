package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.List;

@Data
@UIModel
public class TestSuiteDTO {
    @UINullable
    private Long id;
    private String name;
    @JsonAlias("project_key")
    @UINullable
    private String projectKey;
    private List<FunctionInputDTO> functionInputs;
    private List<SuiteTestDTO> tests;
}
