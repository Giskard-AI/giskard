package ai.giskard.service.dto.ml;

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
    @Getter
    @NotNull
    @UINullable
    private Long id;
    @Getter
    @NotNull
    private String name;
    @Getter
    @NotNull
    @UINullable
    private String key;
    @Getter
    @NotNull
    private String description;

}
