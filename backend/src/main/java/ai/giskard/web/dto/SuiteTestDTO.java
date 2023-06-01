package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import java.util.Map;
import java.util.UUID;

@Data
public class SuiteTestDTO {
    private Map<String, TestInputDTO> testInputs;
    private long id;
    @JsonAlias("test_uuid")
    @NotBlank
    private UUID testUuid;;
    private Map<@NotBlank String, @Valid TestInputDTO> testInputs;
}
