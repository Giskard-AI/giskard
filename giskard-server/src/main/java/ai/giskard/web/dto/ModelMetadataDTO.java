package ai.giskard.web.dto;

import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Builder;
import lombok.Getter;

import java.util.List;
import java.util.Map;

@Getter
@Builder
@UIModel
public class ModelMetadataDTO {
    private Long id;
    private ModelType modelType;
    private Float threshold;
    private Map<String, String> features;
    private String target;
    private List<String> classificationLabels;

}
