package ai.giskard.web.dto;

import lombok.Data;

import javax.validation.constraints.NotBlank;

@Data
public class GenerateTestSuiteInputDTO {
    @NotBlank
    private String name;
    private String value;
    @NotBlank
    private String type;
}
