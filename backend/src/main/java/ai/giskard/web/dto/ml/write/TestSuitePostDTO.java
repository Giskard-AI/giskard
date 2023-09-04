package ai.giskard.web.dto.ml.write;

import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.dto.ml.ProjectDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;

@NoArgsConstructor
@UIModel
public class TestSuitePostDTO  {
    @Setter
    @Getter
    private Long id;

    @Getter
    @Setter
    @NotNull
    private String name;

    @Getter
    @Setter
    private ProjectDTO project;

    @Getter
    @Setter
    private DatasetDTO referenceDataset;

    @Getter
    @Setter
    private DatasetDTO actualDataset;

    @Getter
    @Setter
    private ModelDTO model;
}
