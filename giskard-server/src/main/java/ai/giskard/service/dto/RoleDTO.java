package ai.giskard.service.dto;

import lombok.NoArgsConstructor;

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
    private String name;
}
