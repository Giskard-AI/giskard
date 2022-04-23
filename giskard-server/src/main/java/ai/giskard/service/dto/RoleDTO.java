package ai.giskard.service.dto;

import ai.giskard.domain.User;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.NoArgsConstructor;

import javax.persistence.Column;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

/**
 * A DTO representing a user, with only the public attributes.
 */
@NoArgsConstructor
public class RoleDTO {

    @lombok.Setter
    @lombok.Getter
    private Long id;

    @lombok.Setter
    @lombok.Getter
    @NotNull
    @Size(max = 50)
    @Column(length = 50)
    private String name;


}
