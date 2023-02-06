package ai.giskard.web.dto;

import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@UIModel
public class ModelMetadataDTO {
    private Long id;
    private ModelType modelType;
    private Float threshold;
    private List<String> featureNames;
    private List<String> classificationLabels;
}
