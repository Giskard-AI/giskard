package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

/**
 * Object to return as body in JWT Authentication.
 */
@UIModel
@AllArgsConstructor
public class JWTToken {

    @Getter
    @Setter
    @JsonProperty("id_token")
    private String idToken;
}
