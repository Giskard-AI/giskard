package ai.giskard.web.dto.ml;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@Getter
@UIModel
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class UpdateTestSuiteDTO {
    private Long id;
    @NotNull
    private String name;
    @UINullable
    private String referenceDatasetId;
    @UINullable
    private String actualDatasetId;
    private String modelId;
}
