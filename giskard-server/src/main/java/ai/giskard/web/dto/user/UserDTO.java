package ai.giskard.web.dto.user;

import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Set;
import java.util.stream.Collectors;

/**
 * A DTO representing a user, with only the public attributes.
 */
@NoArgsConstructor
@UIModel
public class UserDTO {

    @Setter
    @Getter
    private Long id;

    @Setter
    @Getter
    @JsonProperty("user_id")
    private String login;

    @Setter
    @Getter
    @JsonProperty("display_name")
    private String displayName;

    @Setter
    @Getter
    private Set<String> roles;

    public UserDTO(User user) {
        this.id = user.getId();
        this.login = user.getLogin();
        this.displayName = user.getDisplayName();
        this.roles = user.getRoles().stream().map(Role::getName).collect(Collectors.toSet());
    }

}
