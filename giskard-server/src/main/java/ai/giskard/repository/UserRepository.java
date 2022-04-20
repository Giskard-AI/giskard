package ai.giskard.repository;

import ai.giskard.domain.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Spring Data JPA repository for the {@link User} entity.
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    default Optional<User> findOneByActivationKey(String activationKey) {
        return Optional.empty();
    }

    //List<User> findAllByActivatedIsFalseAndActivationKeyIsNotNullAndCreatedDateBefore(Instant dateTime);

    default Optional<User> findOneByResetKey(String resetKey) {
        return Optional.empty();
    }

    Optional<User> findOneByEmailIgnoreCase(String email);

    Optional<User> findOneByLogin(String login);

    User getOneByLogin(String login);

    Optional<User> findOneById(Long id);

    @EntityGraph(attributePaths = "roles")
    Optional<User> findOneWithRolesByLogin(String login);

    @EntityGraph(attributePaths = "projects")
    User getOneWithProjectsByLogin(String login);

    @EntityGraph(attributePaths = "roles")
    Optional<User> findOneWithRolesByEmailIgnoreCase(String email);

    Page<User> findAllByIdNotNullAndActivatedIsTrue(Pageable pageable);
}
