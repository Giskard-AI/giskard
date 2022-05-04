package ai.giskard.web.dto.ml;

import ai.giskard.web.dto.user.UserDTO;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class ProjectDTO {
    @Getter
    @NotNull
    private Long id;
    @Getter
    @NotNull
    private String name;
    @Getter
    @JsonProperty("owner_details")
    private UserDTO owner;
    @Getter
    private String key;
    @Getter
    @JsonProperty("guest_list")
    private List<UserDTO> guests;
    @Getter
    @JsonProperty("created_on")
    private LocalDateTime createdOn;
}
