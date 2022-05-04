package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.TestSuite;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@NoArgsConstructor
public class TestSuiteDTO {
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
    private DatasetDTO trainDataset;

    @Getter
    @Setter
    private DatasetDTO testDataset;

    @Getter
    @Setter
    private ModelDTO model;

    public TestSuiteDTO(TestSuite suite) {
        this.setId(suite.getId());
        this.setName(suite.getName());
        if (suite.getTestDataset() != null) {
            this.testDataset = new DatasetDTO(suite.getTestDataset());
        }
        if (suite.getTrainDataset() != null) {
            this.trainDataset = new DatasetDTO(suite.getTrainDataset());
        }
        this.model = new ModelDTO(suite.getModel());
    }
}
