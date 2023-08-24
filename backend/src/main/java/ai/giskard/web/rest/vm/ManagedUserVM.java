package ai.giskard.web.rest.vm;

import ai.giskard.web.dto.user.AdminUserDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;

import jakarta.validation.constraints.Size;

/**
 * View Model extending the AdminUserDTO, which is meant to be used in the user management UI.
 */
@UIModel
public class ManagedUserVM extends AdminUserDTO {

    public static final int PASSWORD_MIN_LENGTH = 4;

    public static final int PASSWORD_MAX_LENGTH = 100;

    @Getter
    @Setter
    @Size(min = PASSWORD_MIN_LENGTH, max = PASSWORD_MAX_LENGTH)
    private String password;

    @Getter
    @Setter
    private String token;
}
