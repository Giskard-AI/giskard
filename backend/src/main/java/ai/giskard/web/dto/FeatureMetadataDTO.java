package ai.giskard.web.dto;

import ai.giskard.domain.ColumnType;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;

import java.util.Set;

@Getter
@Setter
@UIModel
public class FeatureMetadataDTO {
    private String name;
    private ColumnType type;
    private Set<String> values;
}
