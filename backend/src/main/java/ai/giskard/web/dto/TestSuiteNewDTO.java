package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.List;

@Data
@UIModel
public class TestSuiteNewDTO {
    private String name;
    @JsonAlias("project_key")
    private String projectKey;
    private List<SuiteTestDTO> tests;
}
