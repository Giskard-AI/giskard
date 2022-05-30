package ai.giskard.domain;
import ai.giskard.config.Constants;
import com.fasterxml.jackson.annotation.JsonIdentityInfo;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.ObjectIdGenerators;
import lombok.Getter;
import lombok.Setter;
import org.apache.commons.lang3.StringUtils;
import org.hibernate.annotations.BatchSize;
import javax.persistence.*;
import javax.validation.constraints.Email;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;
import java.time.Instant;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
/**
 * A user.
 */
@Entity
@Table(name = "giskard_users")
@Getter
@Setter
@NotNull
@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
public class User extends AbstractAuditingEntity {
    @Pattern(regexp = Constants.LOGIN_REGEX)
    @Size(min = 1, max = 50)
    @Column(name = "user_id", length = 50, unique = true, nullable = false)
    private String login;

    @JsonIgnore
    @NotNull
    @Size(min = 60, max = 60)
    @Column(name = "hashed_password", length = 60, nullable = false)
    private String password;

    @Size(max = 150)
    @Column(length = 150)
    private String displayName;

    @Email
    @Size(min = 5, max = 254)
    @Column(length = 254, unique = true)
    private String email;

    @NotNull
    @Column(name = "is_active", nullable = false)
    private boolean activated = false;

    @NotNull
    @Column(nullable = false)
    private boolean enabled = false;

    @Size(max = 20)
    @Column(name = "activation_key", length = 20)
    @JsonIgnore
    private String activationKey;

    @Size(max = 20)
    @Column(name = "reset_key", length = 20)
    @JsonIgnore
    private String resetKey;

    @Column(name = "reset_date")
    private Instant resetDate = null;

    @JsonIgnore
    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(
        name = "giskard_user_role",
        joinColumns = {@JoinColumn(name = "user_id", referencedColumnName = "id")},
        inverseJoinColumns = {@JoinColumn(name = "role_name", referencedColumnName = "name")}
    )
    @BatchSize(size = 20)
    private Set<Role> roles = new HashSet<>();
    // Lowercase the login before saving it in database
    public void setLogin(String login) {
        this.login = StringUtils.lowerCase(login, Locale.ENGLISH);
    }
    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof User)) {
            return false;
        }
        return getId() != null && getId().equals(((User) o).getId());
    }
    @Override
    public int hashCode() {
        // see https://vladmihalcea.com/how-to-implement-equals-and-hashcode-using-the-jpa-entity-identifier/
        return getClass().hashCode();
    }
    @Override
    public String toString() {
        return "User{" +
            "id=" + getId() +
            ", login='" + login + '\'' +
            '}';
    }

    @JsonIgnore
    @ManyToMany(mappedBy = "guests", cascade = CascadeType.ALL)
    private Set<Project> projects = new HashSet<>();
    public String getDisplayNameOrLogin() {
        return displayName != null ? displayName : login;
    }
}
