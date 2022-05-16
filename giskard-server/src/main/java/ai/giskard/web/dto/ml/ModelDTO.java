package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.ModelLanguage;
import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

@Getter
@Setter
@UIModel
@NoArgsConstructor
public class ModelDTO extends FileDTO {
    private String languageVersion;
    private ModelLanguage language;
    private ModelType modelType;
    private Float threshold;
    private String features;
    private String target;
    private String classificationLabels;
    private String requirementsFileName;
}
