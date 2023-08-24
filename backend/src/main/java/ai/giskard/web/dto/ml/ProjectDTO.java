package ai.giskard.web.dto.ml;

import ai.giskard.domain.MLWorkerType;
import ai.giskard.web.dto.user.UserDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;
import java.time.Instant;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class ProjectDTO {
    @NotNull
    private Long id;
    @NotNull
    private String name;
    private UserDTO owner;
    private String key;
    private String description;
    private List<UserDTO> guests;
    private Instant createdDate;
    private MLWorkerType mlWorkerType;
}
