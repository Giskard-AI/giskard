package ai.giskard.repository;

import ai.giskard.domain.Role;

import java.util.Optional;

/**
 * Spring Data JPA repository for the {@link Role} entity.
 */
public interface RoleRepository extends MappableJpaRepository<Role, String> {
    Optional<Role> findByName(String name);
}
