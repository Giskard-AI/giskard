package ai.giskard.web.dto;

import lombok.Getter;

@Getter
public class GenerateTestDatasetInputDTO extends GenerateTestSuiteInputDTO {
    private String target;
}
