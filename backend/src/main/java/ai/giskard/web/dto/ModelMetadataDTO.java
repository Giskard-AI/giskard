package ai.giskard.web.dto;

import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Builder;
import lombok.Getter;

import java.util.List;
import java.util.UUID;

@Getter
@Builder
@UIModel
public class ModelMetadataDTO {
    private UUID id;
    private ModelType modelType;
    private Float threshold;
    private List<String> featureNames;
    private List<String> classificationLabels;
}
