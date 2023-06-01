package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.List;

@Data
public class TestSuiteNewDTO {
    private String name;
    @JsonAlias("project_key")
    private String projectKey;
    private List<SuiteTestDTO> tests;
}
