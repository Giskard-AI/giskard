package ai.giskard.domain;

import ai.giskard.config.Constants;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.io.Serializable;
import java.time.Instant;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import javax.persistence.*;
import javax.validation.constraints.Email;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;
import org.apache.commons.lang3.StringUtils;
import org.hibernate.annotations.BatchSize;

/**
 * A user.
 */
@Entity
@Table(name = "jhi_user")
public class User extends AbstractAuditingEntity implements Serializable {

    private static final long serialVersionUID = 1L;

    @lombok.Setter
    @lombok.Getter
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "sequenceGenerator")
    @SequenceGenerator(name = "sequenceGenerator")
    private Long id;

    @lombok.Getter
    @NotNull
    @Pattern(regexp = Constants.LOGIN_REGEX)
    @Size(min = 1, max = 50)
    @Column(length = 50, unique = true, nullable = false)
    private String login;

    @lombok.Setter
    @lombok.Getter
    @JsonIgnore
    @NotNull
    @Size(min = 60, max = 60)
    @Column(name = "password_hash", length = 60, nullable = false)
    private String password;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 150)
    @Column(name = "display_name", length = 150)
    private String displayName;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 50)
    @Column(name = "first_name", length = 50)
    private String firstName;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 50)
    @Column(name = "last_name", length = 50)
    private String lastName;

    @lombok.Setter
    @lombok.Getter
    @Email
    @Size(min = 5, max = 254)
    @Column(length = 254, unique = true)
    private String email;

    @lombok.Setter
    @lombok.Getter
    @NotNull
    @Column(nullable = false)
    private boolean activated = false;

    @lombok.Setter
    @lombok.Getter
    @Size(min = 2, max = 10)
    @Column(name = "lang_key", length = 10)
    private String langKey;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 256)
    @Column(name = "image_url", length = 256)
    private String imageUrl;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 20)
    @Column(name = "activation_key", length = 20)
    @JsonIgnore
    private String activationKey;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 20)
    @Column(name = "reset_key", length = 20)
    @JsonIgnore
    private String resetKey;

    @lombok.Setter
    @lombok.Getter
    @Column(name = "reset_date")
    private Instant resetDate = null;

    @lombok.Setter
    @lombok.Getter
    @JsonIgnore
    @ManyToMany
    @JoinTable(
        name = "jhi_user_role",
        joinColumns = { @JoinColumn(name = "user_id", referencedColumnName = "id") },
        inverseJoinColumns = { @JoinColumn(name = "role_name", referencedColumnName = "name") }
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
        return id != null && id.equals(((User) o).id);
    }

    @Override
    public int hashCode() {
        // see https://vladmihalcea.com/how-to-implement-equals-and-hashcode-using-the-jpa-entity-identifier/
        return getClass().hashCode();
    }

}
