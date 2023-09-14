package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.ModelLanguage;
import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Getter
@Setter
@UIModel
@NoArgsConstructor
@AllArgsConstructor
public class ModelDTO {
    @JsonAlias("language_version")
    private String languageVersion;
    private ModelLanguage language;
    @JsonAlias("model_type")
    private ModelType modelType;
    private Float threshold;
    @UINullable
    @JsonAlias("feature_names")
    private List<String> featureNames;
    @JsonAlias("classification_labels")
    private List<String> classificationLabels;
    private String classificationLabelsDtype;

    @JsonProperty("id")
    @NotNull
    private UUID id;

    @JsonIgnore
    private ProjectDTO project;

    private String name;

    @JsonAlias("created_date")
    private Instant createdDate;

    private long size;

    public Long getProjectId() {
        return project == null ? null : project.getId();
    }
}
