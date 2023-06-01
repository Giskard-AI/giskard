package ai.giskard.web.dto.ml;

import ai.giskard.domain.InspectionSettings;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class ProjectPostDTO {
    @UINullable
    private Long id;

    @NotNull
    private String name;

    @NotNull
    private InspectionSettings inspectionSettings = new InspectionSettings();

    @NotNull
    @UINullable
    private String key;
    private String description;
}
