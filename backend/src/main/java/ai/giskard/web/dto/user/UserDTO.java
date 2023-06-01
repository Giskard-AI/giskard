package ai.giskard.web.dto.user;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Set;

/**
 * A DTO representing a user, with only the public attributes.
 */
@UIModel
@Getter
@Setter
@NoArgsConstructor
public class UserDTO {
    private Long id;
    @JsonProperty("user_id")
    private String login;
    private String displayName;
    private Set<String> roles;
}
