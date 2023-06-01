package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.Map;

@Data
public class SuiteTestDTO {
    private Map<String, TestInputDTO> testInputs;
    private TestFunctionDTO testFunction;

}
