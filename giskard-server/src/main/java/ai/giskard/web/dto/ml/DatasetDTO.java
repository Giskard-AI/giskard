package ai.giskard.web.dto.ml;

import ai.giskard.domain.FeatureType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class DatasetDTO extends FileDTO {
    private String target;
    private Map<String, FeatureType> featureTypes;
}
