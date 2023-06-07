package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import lombok.Data;

import javax.validation.constraints.NotBlank;

@Data
@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    property = "suiteInputType"
)
@JsonSubTypes({
    @JsonSubTypes.Type(value = GenerateTestSuiteInputDTO.class, name = "suite"),
    @JsonSubTypes.Type(value = GenerateTestModelInputDTO.class, name = "model"),
    @JsonSubTypes.Type(value = GenerateTestDatasetInputDTO.class, name = "dataset")
})
public class GenerateTestSuiteInputDTO {
    @NotBlank
    private String name;
    @NotBlank
    private String type;
}
