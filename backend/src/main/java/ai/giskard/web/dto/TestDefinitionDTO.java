package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class TestDefinitionDTO {
    private String id;
    private String name;
    private String module;
    private String doc;
    @JsonAlias("module_doc")
    private String moduleDoc;
    private Map<String, TestFunctionArgumentDTO> arguments;
    private List<String> tags;
    private String code;
}
