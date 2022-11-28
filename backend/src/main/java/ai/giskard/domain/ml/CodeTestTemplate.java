package ai.giskard.domain.ml;

import java.util.Set;

public class CodeTestTemplate {
    public String id;
    public String title;
    public String hint;
    public String code;
    public Set<ModelType> modelTypes;
    public boolean isMultipleDatasets;
    public boolean isGroundTruthRequired;
    public boolean enabled = true;
}
