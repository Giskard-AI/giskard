package ai.giskard.web.dto.ml;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.time.Instant;

@Getter
@UIModel
@Setter
@NoArgsConstructor
public class SliceDTO {
    @JsonProperty("id")
    @NotNull
    private Long id;
    @NotNull
    private String name;
    private ProjectDTO project;
    private String code;
    private Instant createdDate;
}
