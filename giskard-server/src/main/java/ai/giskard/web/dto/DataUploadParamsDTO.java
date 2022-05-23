package ai.giskard.web.dto;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@UIModel
@Getter
@Setter
@NoArgsConstructor
public class DataUploadParamsDTO {
    private String name;
    private String projectKey;
    private Map<String, FeatureType> featureTypes;
    private String target;
}
