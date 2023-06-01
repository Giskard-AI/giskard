package ai.giskard.web.dto;

import ai.giskard.domain.ml.ModelLanguage;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

import java.util.List;

@UIModel
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ModelUploadParamsDTO {
    private String name;
    private String projectKey;
    private String languageVersion;
    private String modelType;
    private Float threshold;
    private List<String> featureNames;
    private ModelLanguage language;
    private List<String> classificationLabels;
}
