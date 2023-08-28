package ai.giskard.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.Objects;

/**
 * An authority (a security role) used by Spring Security.
 */
@Entity
@Table(name = "role")
public class Role extends BaseEntity {
    @lombok.Setter
    @lombok.Getter
    @NotNull
    @Size(max = 50)
    @Column(length = 50, unique = true)
    private String name;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Role role = (Role) o;
        return getId().equals(role.getId()) && name.equals(role.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(getId(), name);
    }
}
