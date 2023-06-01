package ai.giskard.web.dto.user;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

/**
 * A DTO representing a user, with only the public attributes.
 */
@NoArgsConstructor
@AllArgsConstructor
@UIModel
public class RoleDTO {

    @lombok.Setter
    @lombok.Getter
    private String id;

    @lombok.Setter
    @lombok.Getter
    @NotNull
    @Size(max = 50)
    private String name;
}
