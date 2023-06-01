package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Data;

import java.util.List;

@UIModel
@Data
public class RunAdHocTransformationDTO {
    private List<FunctionInputDTO> functionInputs;
    @UINullable
    private List<Integer> rows;
}
