package ai.giskard.web.dto;

import ai.giskard.domain.ml.ModelLanguage;
import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.*;

import java.util.List;

@UIModel
@Getter
@Setter
@Builder
@AllArgsConstructor
public class ModelUploadParamsDTO {
    private String name;
    private String projectKey;
    private String languageVersion;
    private String modelType;
    private Float threshold;
    private List<String> featureNames;
    private ModelLanguage language;
    private List<String> classificationLabels;

    public ModelUploadParamsDTO() {
    }
}
