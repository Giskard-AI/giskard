package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import java.util.Map;

@Data
public class SuiteTestDTO {
    @JsonAlias("test_id")
    @NotBlank
    private String testId;
    private Map<@NotBlank String, @Valid TestInputDTO> testInputs;
}
