package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.Map;
import java.util.UUID;

@Data
public class SuiteTestDTO {
    @UINullable
    private long id;

    private TestFunctionDTO testFunction;

    @JsonAlias("test_uuid")
    @NotNull
    private UUID testUuid;
    private Map<@NotBlank String, @Valid TestInputDTO> testInputs;
}
