package ai.giskard.web.dto.user;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Size;

/**
 * A DTO representing a user, with his authorities.
 */
@NoArgsConstructor
@UIModel
public class UpdateMeDTO {

    @Setter
    @Getter
    @Email
    @Size(min = 5, max = 254)
    @UINullable
    private String email;

    @Setter
    @Getter
    @Size(max = 150)
    @UINullable
    private String displayName;

    @Setter
    @Getter
    @UINullable
    private String password;
}
