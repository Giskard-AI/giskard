package ai.giskard.service.dto.ml;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;

@Getter
@Setter
@NoArgsConstructor
public class ProjectPostDTO {
    @Getter
    @NotNull
    private Long id;
    @Getter
    @NotNull
    private String name;
    @Getter
    @NotNull
    private String key;

}
