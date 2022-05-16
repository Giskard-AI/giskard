package ai.giskard.web.dto;

import ai.giskard.domain.ml.ModelLanguage;
import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@UIModel
@Getter
@Setter
@NoArgsConstructor
public class ModelUploadParamsDTO {
    private String name;
    private String projectKey;
    private String languageVersion;
    private ModelType modelType;
    private Float threshold;
    private String features;
    private String target;
    private ModelLanguage language;
    private String classificationLabels;

    public void setClassificationLabels(Object obj) throws JsonProcessingException {
        this.classificationLabels = new ObjectMapper().writeValueAsString(obj);
    }
    public void setFeatures(Object obj) throws JsonProcessingException {
        this.features = new ObjectMapper().writeValueAsString(obj);
    }
}
