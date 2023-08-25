package ai.giskard.web.dto.user;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/**
 * A DTO representing a user, with only the public attributes.
 */
@NoArgsConstructor
@AllArgsConstructor
@Setter
@Getter
@UIModel
public class RoleDTO {

    @Setter
    @Getter
    private String id;

    @Setter
    @Getter
    @NotNull
    @Size(max = 50)
    private String name;
}
