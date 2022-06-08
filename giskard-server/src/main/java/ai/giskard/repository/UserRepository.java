package ai.giskard.repository;

import ai.giskard.domain.User;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Spring Data JPA repository for the {@link User} entity.
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    default Optional<User> findOneByActivationKey(String activationKey) {
        return Optional.empty();
    }

    @EntityGraph(attributePaths = "roles")
    List<User> getAllWithRolesByLoginNot(String login);

    Optional<User> findOneByResetKey(String resetKey);

    Optional<User> findOneByEmailIgnoreCase(String email);

    Optional<User> findOneByLogin(String login);


    default User getOneByLogin(String login) {
        return this.findOneByLogin(login).orElseThrow(() -> new EntityNotFoundException(Entity.USER, EntityNotFoundException.By.LOGIN, login));
    }

    Optional<User> findOneById(Long id);

    @EntityGraph(attributePaths = "roles")
    Optional<User> findOneWithRolesByLogin(String login);

    @EntityGraph(attributePaths = "roles")
    Optional<User> findOneWithRolesById(Long id);

    @EntityGraph(attributePaths = "projects")
    User getOneWithProjectsByLogin(String login);

    @EntityGraph(attributePaths = "roles")
    Optional<User> findOneWithRolesByEmailIgnoreCase(String email);

    Page<User> findAllByIdNotNullAndActivatedIsTrue(Pageable pageable);

    List<User> findAllByIdNotNullAndActivatedIsTrue();
}
