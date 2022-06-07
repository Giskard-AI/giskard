package ai.giskard.domain.ml;

import lombok.Getter;
import lombok.Setter;

import java.util.Set;

@Getter
@Setter
public class CodeTestTemplate {
    private String id;
    private String title;
    private String hint;
    private String code;
    private Set<ModelType> modelTypes;
    boolean isMultipleDatasets;
    boolean isGroundTruthRequired;
}
