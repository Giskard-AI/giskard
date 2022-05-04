package ai.giskard.web.dto.user;

import ai.giskard.config.Constants;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;
import java.time.Instant;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * A DTO representing a user, with his authorities.
 */
@NoArgsConstructor
@UIModel
public class AdminUserDTO {
    @NoArgsConstructor
    @AllArgsConstructor
    @UIModel
    public static class AdminUserDTOWithPassword extends AdminUserDTO {
        @Setter
        @Getter
        private String password;

        public AdminUserDTOWithPassword(User user) {
            super(user);
        }
    }

    @Setter
    @Getter
    @UINullable
    private Long id;

    @Setter
    @Getter
    @NotBlank
    @Pattern(regexp = Constants.LOGIN_REGEX)
    @Size(min = 1, max = 50)
    @JsonProperty("user_id")
    private String login;

    @Setter
    @Getter
    @Size(max = 50)
    @UINullable
    private String firstName;

    @Setter
    @Getter
    @Size(max = 50)
    @UINullable
    private String lastName;

    @Setter
    @Getter
    @Size(max = 150)
    @JsonProperty("display_name")
    @UINullable
    private String displayName;

    @Setter
    @Getter
    @Email
    @Size(min = 5, max = 254)
    private String email;

    @Setter
    @Getter
    @Size(max = 256)
    @UINullable
    private String imageUrl;

    @Setter
    @Getter
    @UINullable
    private boolean enabled = false;

    @Setter
    @Getter
    @UINullable
    private boolean activated = false;

    @Setter
    @Getter
    @Size(min = 2, max = 10)
    @UINullable
    private String langKey;

    @Setter
    @Getter
    @UINullable
    private String createdBy;

    @Setter
    @Getter
    @UINullable
    private Instant createdDate;

    @Setter
    @Getter
    @UINullable
    private String lastModifiedBy;

    @Setter
    @Getter
    @UINullable
    private Instant lastModifiedDate;

    @Setter
    @Getter
    @UINullable
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
        this.enabled = user.isEnabled();
        this.imageUrl = user.getImageUrl();
        this.langKey = user.getLangKey();
        this.createdBy = user.getCreatedBy();
        this.createdDate = user.getCreatedDate();
        this.lastModifiedBy = user.getLastModifiedBy();
        this.lastModifiedDate = user.getLastModifiedDate();
        this.roles = user.getRoles().stream().map(Role::getName).collect(Collectors.toSet());
    }
}
