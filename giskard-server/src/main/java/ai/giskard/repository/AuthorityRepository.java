package ai.giskard.repository;

import ai.giskard.domain.Role;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Spring Data JPA repository for the {@link Role} entity.
 */
public interface AuthorityRepository extends JpaRepository<Role, String> {}
