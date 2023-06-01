package ai.giskard.web.dto.ml;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
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
    @JsonAlias("feature_types")
    private Map<String, FeatureType> featureTypes;
    @JsonIgnore
    private ProjectDTO project;
    @JsonProperty("id")
    @NotNull
    private String id;
    private String name;
    @JsonAlias("column_types")
    private Map<String, String> columnTypes;
    @JsonAlias("original_size_bytes")
    private int originalSizeBytes;
    @JsonAlias("compressed_size_bytes")
    private int compressedSizeBytes;

    @JsonAlias("created_date")
    private Instant createdDate;
}
