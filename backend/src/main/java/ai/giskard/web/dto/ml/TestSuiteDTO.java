package ai.giskard.web.dto.ml;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@Getter
@UIModel
@Setter
@NoArgsConstructor
public class TestSuiteDTO {
    private Long id;
    @NotNull
    private String name;
    private ProjectDTO project;
    private DatasetDTO referenceDataset;
    private DatasetDTO actualDataset;
    private ModelDTO model;
}
