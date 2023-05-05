package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

@Data
@AllArgsConstructor
@NoArgsConstructor
@UIModel
public class ParameterizedCallableDTO {
    @NotNull
    private UUID uuid;
    private List<FunctionInputDTO> params;
    @NotNull
    private String type;
}
