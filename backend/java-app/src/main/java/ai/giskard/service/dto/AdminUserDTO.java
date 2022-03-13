package ai.giskard.service.dto;

import ai.giskard.config.Constants;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.NoArgsConstructor;

import javax.persistence.Column;
import javax.validation.constraints.*;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * A DTO representing a user, with his authorities.
 */
@NoArgsConstructor
public class AdminUserDTO {
    public static class AdminUserDTOWithPassword extends AdminUserDTO{
        @lombok.Setter
        @lombok.Getter
        @NotNull
        private String password;
    }

    @lombok.Setter
    @lombok.Getter
    private Long id;

    @lombok.Setter
    @lombok.Getter
    @NotBlank
    @Pattern(regexp = Constants.LOGIN_REGEX)
    @Size(min = 1, max = 50)
    @JsonProperty("user_id")
    private String login;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 50)
    private String firstName;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 50)
    private String lastName;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 150)
    @JsonProperty("display_name")
    private String displayName;

    @lombok.Setter
    @lombok.Getter
    @Email
    @Size(min = 5, max = 254)
    private String email;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 256)
    private String imageUrl;

    @lombok.Setter
    @lombok.Getter
    @JsonProperty("is_active")
    private boolean activated = false;

    @lombok.Setter
    @lombok.Getter
    @Size(min = 2, max = 10)
    private String langKey;

    @lombok.Setter
    @lombok.Getter
    private String createdBy;

    @lombok.Setter
    @lombok.Getter
    private Instant createdDate;

    @lombok.Setter
    @lombok.Getter
    private String lastModifiedBy;

    @lombok.Setter
    @lombok.Getter
    private Instant lastModifiedDate;

    @lombok.Setter
    @lombok.Getter
    private Set<String> roles;

    //@JsonProperty("display_name")
    //public String displayName() {
    //    return Stream.of(firstName, lastName)
    //        .filter(s -> s != null && !s.isEmpty())
    //        .collect(Collectors.joining(" "));
    //}

    public AdminUserDTO(User user) {
        this.id = user.getId();
        this.login = user.getLogin();
        this.firstName = user.getFirstName();
        this.lastName = user.getLastName();
        this.displayName = user.getDisplayName();
        this.email = user.getEmail();
        this.activated = user.isActivated();
        this.imageUrl = user.getImageUrl();
        this.langKey = user.getLangKey();
        this.createdBy = user.getCreatedBy();
        this.createdDate = user.getCreatedDate();
        this.lastModifiedBy = user.getLastModifiedBy();
        this.lastModifiedDate = user.getLastModifiedDate();
        this.roles = user.getRoles().stream().map(Role::getName).collect(Collectors.toSet());
    }

}
