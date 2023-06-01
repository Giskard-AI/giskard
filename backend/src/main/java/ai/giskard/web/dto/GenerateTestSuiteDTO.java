package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Data;

@Data
@UIModel
public class GenerateTestSuiteDTO {
    private String name;
    @UINullable
    private String model;
    @UINullable
    private String actualDataset;
    @UINullable
    private String referenceDataset;
}
