package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.Map;

@Data
public class SuiteTestDTO {
    @JsonAlias("test_id")
    private String testId;
    private Map<String, TestInputDTO> testInputs;
}
