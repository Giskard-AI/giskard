package ai.giskard.web.dto.user;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.NoArgsConstructor;

/**
 * A DTO representing a user, with only the public attributes.
 */
@NoArgsConstructor
@UIModel
public class UserMinimalDTO {
    public Long id;
    @JsonProperty("user_id")
    public String login;
    public String displayName;
}
