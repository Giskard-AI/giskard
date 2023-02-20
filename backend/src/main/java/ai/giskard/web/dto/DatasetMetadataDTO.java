package ai.giskard.web.dto;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class DatasetMetadataDTO {
    Long id;
    @UINullable
    private String target;
    private Map<String, FeatureType> featureTypes;
    @UINullable
    private Map<String, String> columnTypes;
}
