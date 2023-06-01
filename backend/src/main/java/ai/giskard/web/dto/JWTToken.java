package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

import java.time.Instant;

/**
 * Object to return as body in JWT Authentication.
 */
@UIModel
@Getter
@Setter
@AllArgsConstructor
public class JWTToken {

    @JsonProperty("id_token")
    private String token;

    private Instant expiryDate;
}
