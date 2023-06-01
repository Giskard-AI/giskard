package ai.giskard.web.dto.ml;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.time.Instant;
import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class DatasetDTO {
    @UINullable
    private String target;
    private Map<String, FeatureType> featureTypes;
    @JsonIgnore
    private ProjectDTO project;
    @JsonProperty("id")
    @NotNull
    private String id;
    private String name;
    private Map<String, String> columnTypes;
    private int originalSizeBytes;
    private int compressedSizeBytes;

    private Instant createdDate;
}
