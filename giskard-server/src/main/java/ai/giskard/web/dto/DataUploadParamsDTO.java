package ai.giskard.web.dto;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

import java.util.Map;

@UIModel
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class DataUploadParamsDTO {
    private String name;
    private String projectKey;
    private Map<String, FeatureType> featureTypes;
    private Map<String, String> columnTypes;
    private String target;
}
