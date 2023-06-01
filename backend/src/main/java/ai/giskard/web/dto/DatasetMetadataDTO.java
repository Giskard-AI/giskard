package ai.giskard.web.dto;

import java.util.Map;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;

import ai.giskard.domain.FeatureType;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class DatasetMetadataDTO {
    String id;
    @UINullable
    private String target;
    private Map<String, FeatureType> featureTypes;
    @UINullable
    private Map<String, String> columnTypes;
}
