package ai.giskard.web.dto.ml;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class InspectionDTO {
    private Long id;
    private DatasetDTO dataset;
    private ModelDTO model;
}
