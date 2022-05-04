package ai.giskard.repository;

import ai.giskard.domain.Role;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

/**
 * Spring Data JPA repository for the {@link Role} entity.
 */
public interface AuthorityRepository extends JpaRepository<Role, String> {
    Optional<Role> findByName(String name);
}
