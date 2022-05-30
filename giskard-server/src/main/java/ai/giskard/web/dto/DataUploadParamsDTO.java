package ai.giskard.web.dto;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

import java.util.Map;

@UIModel
@Getter
@Setter
@AllArgsConstructor
@Builder
public class DataUploadParamsDTO {
    private String name;
    private String projectKey;
    private Map<String, FeatureType> featureTypes;
    private String target;
}
