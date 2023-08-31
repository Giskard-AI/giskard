package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Data;

import jakarta.validation.constraints.NotNull;
import java.util.List;

@Data
@UIModel
public class GenerateTestSuiteDTO {
    private String name;
    @NotNull
    private List<@NotNull GenerateTestSuiteInputDTO> inputs;

    @NotNull
    private List<@NotNull FunctionInputDTO> sharedInputs;
}
