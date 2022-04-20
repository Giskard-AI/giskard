package ai.giskard.domain;

import ai.giskard.config.Constants;
import com.fasterxml.jackson.annotation.JsonIdentityInfo;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.ObjectIdGenerators;
import org.apache.commons.lang3.StringUtils;
import org.hibernate.annotations.BatchSize;

import javax.persistence.*;
import javax.validation.constraints.Email;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;
import java.io.Serializable;
import java.time.Instant;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * A user.
 */
@Entity
@Table(name = "\"user\"")
@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class,property = "id")
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
    @Column(name = "user_id", length = 50, unique = true, nullable = false)
    private String login;

    @lombok.Setter
    @lombok.Getter
    @JsonIgnore
    @NotNull
    @Size(min = 60, max = 60)
    @Column(name = "hashed_password", length = 60, nullable = false)
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
    @Transient
    private String firstName;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 50)
    @Column(name = "last_name", length = 50)
    @Transient
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
    @Column(name = "is_active", nullable = false)
    private boolean activated = false;

    @lombok.Setter
    @lombok.Getter
    @Size(min = 2, max = 10)
    @Column(name = "lang_key", length = 10)
    @Transient
    private String langKey;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 256)
    @Column(name = "image_url", length = 256)
    @Transient
    private String imageUrl;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 20)
    @Column(name = "activation_key", length = 20)
    @JsonIgnore
    @Transient
    private String activationKey;

    @lombok.Setter
    @lombok.Getter
    @Size(max = 20)
    @Column(name = "reset_key", length = 20)
    @JsonIgnore
    @Transient
    private String resetKey;

    @lombok.Setter
    @lombok.Getter
    @Column(name = "reset_date")
    @Transient
    private Instant resetDate = null;

    @lombok.Setter
    @lombok.Getter
    //@JsonIgnore
    @ManyToOne()
    @BatchSize(size = 20)
    private Role role;

    // Lowercase the login before saving it in database
    public void setLogin(String login) {
        this.login = StringUtils.lowerCase(login, Locale.ENGLISH);
    }

    // TODO andreyavtomonov (14/03/2022): migration
    public Set<Role> getRoles() {
        return Collections.singleton(role);
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

    @lombok.Setter
    @lombok.Getter
    @JsonIgnore
    @ManyToMany()
    @JoinTable(
        name = "projects_guests",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns =  @JoinColumn(name = "project_id"))
    private List<Project> projects;



    //// TODO andreyavtomonov (14/03/2022): remove after inge
    //public String getCreatedBy() {
    //    return null;
    //}
    //
    //public void setCreatedBy(String createdBy) {
    //}
    //
    //public Instant getCreatedDate() {
    //    return null;
    //}
    //
    //public void setCreatedDate(Instant createdDate) {
    //}
    //
    //public String getLastModifiedBy() {
    //    return null;
    //}
    //
    //public void setLastModifiedBy(String lastModifiedBy) {
    //}
    //
    //public Instant getLastModifiedDate() {
    //    return null;
    //}
    //
    //public void setLastModifiedDate(Instant lastModifiedDate) {
    //}

}
