package ai.giskard.web.dto.user;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.Email;
import javax.validation.constraints.Size;
import java.util.Set;

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
