package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
@UIModel
public class TestSuiteCreateDTO {
    private Long projectId;
    @UINullable
    private Long trainDatasetId;
    @UINullable
    private Long testDatasetId;
    private Long modelId;
    private String name;
    private boolean shouldGenerateTests;
}
