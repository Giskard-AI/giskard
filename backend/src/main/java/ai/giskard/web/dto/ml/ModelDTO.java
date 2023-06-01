package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.ModelLanguage;
import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@UIModel
@NoArgsConstructor
public class ModelDTO extends FileDTO {
    private String languageVersion;
    private ModelLanguage language;
    private ModelType modelType;
    private Float threshold;
    @UINullable
    private List<String> featureNames;
    private List<String> classificationLabels;
    private String requirementsFileName;
}
