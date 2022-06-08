package ai.giskard.repository;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

import static ai.giskard.web.rest.errors.EntityNotFoundException.By;

@Repository
public interface ProjectRepository extends MappableJpaRepository<Project, Long> {
    @EntityGraph(attributePaths = "guests")
    Optional<Project> findOneWithGuestsById(Long id);

    List<Project> getProjectsByOwnerOrGuestsContains(User owner, User guest);

    default Project getOneByName(String name) {
        return findOneByName(name).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, By.NAME, name));
    }

    Optional<Project> findOneByKey(String key);

    default Project getOneByKey(String key) {
        return findOneByKey(key).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, By.KEY, key));
    }

    Optional<Project> findOneByName(String name);
}
