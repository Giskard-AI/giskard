package ai.giskard.web.dto;

import lombok.Getter;

@Getter
public class GenerateTestModelInputDTO extends GenerateTestSuiteInputDTO {
    private String modelType;
}
