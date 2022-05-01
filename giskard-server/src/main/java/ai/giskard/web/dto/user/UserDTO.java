package ai.giskard.web.dto.user;

import ai.giskard.domain.User;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.NoArgsConstructor;

/**
 * A DTO representing a user, with only the public attributes.
 */
@NoArgsConstructor
@UIModel
public class UserDTO {

    @lombok.Setter
    @lombok.Getter
    private Long id;

    @lombok.Setter
    @lombok.Getter
    @JsonProperty("user_id")
    private String login;

    @lombok.Setter
    @lombok.Getter
    @JsonProperty("display_name")
    private String displayName;

    public UserDTO(User user) {
        this.id = user.getId();
        // Customize it here if you need, or not, firstName/lastName/etc
        this.login = user.getLogin();
        this.displayName = user.getDisplayName();
    }

}
