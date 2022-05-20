package ai.giskard.web.dto.ml;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class DatasetDTO extends FileDTO {
    private String target;
    private String featureTypes;
}
