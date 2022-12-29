package ai.giskard.web.dto;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@UIModel
@AllArgsConstructor
public class DatasetMetadataDTO {
    private String name;
    private UUID id;
    @UINullable
    private String target;
    @JsonAlias("feature_types")
    private Map<String, FeatureType> featureTypes;
    @UINullable
    @JsonAlias("column_types")
    private Map<String, String> columnTypes;
}
