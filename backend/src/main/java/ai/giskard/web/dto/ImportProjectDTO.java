package ai.giskard.web.dto;

import ai.giskard.web.dto.ml.ProjectDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;


@UIModel
@Getter
@Setter
@AllArgsConstructor
public class ImportProjectDTO {
    private boolean isConflict;

    ProjectDTO project;

    String pathImportTmp;
}
