package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
@UIModel
public class CatalogDTO {
    private List<TestFunctionDTO> tests = new ArrayList<>();
    private List<SlicingFunctionDTO> slices = new ArrayList<>();
    private List<TransformationFunctionDTO> transformations = new ArrayList<>();
}
