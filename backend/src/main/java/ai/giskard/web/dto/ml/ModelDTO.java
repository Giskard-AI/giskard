package ai.giskard.web.dto.ml;

import ai.giskard.domain.ml.ModelLanguage;
import ai.giskard.domain.ml.ModelType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.List;

@Getter
@Setter
@UIModel
@NoArgsConstructor
@AllArgsConstructor
public class ModelDTO {
    private String languageVersion;
    private ModelLanguage language;
    private ModelType modelType;
    private Float threshold;
    @UINullable
    private List<String> featureNames;
    private List<String> classificationLabels;

    @JsonProperty("id")
    @NotNull
    private String id;

    @JsonIgnore
    private ProjectDTO project;

    private String name;

    private Instant createdDate;

    private long size;

    public String getName() {
        return name != null ? name : id;
    }

    public Long getProjectId() {
        return project == null ? null : project.getId();
    }
}
