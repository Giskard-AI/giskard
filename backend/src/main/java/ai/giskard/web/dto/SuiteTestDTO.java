package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.Map;
import java.util.UUID;

@Data
public class SuiteTestDTO {
    @UINullable
    private long id;
    @JsonAlias("test_uuid")
    @NotNull
    private UUID testUuid;
    private TestFunctionDTO test;
    private Map<@NotBlank String, @Valid FunctionInputDTO> functionInputs;
}
