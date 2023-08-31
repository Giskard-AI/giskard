package ai.giskard.repository;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.mapstruct.Named;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

import static ai.giskard.web.rest.errors.EntityNotFoundException.By;

@Repository
public interface ProjectRepository extends MappableJpaRepository<Project, Long> {
    @Override
    default Entity getEntityType() {
        return Entity.PROJECT;
    }

    @EntityGraph(attributePaths = "guests")
    Optional<Project> findOneWithGuestsById(Long id);

    @EntityGraph(attributePaths = {"guests", "owner"})
    Optional<Project> findOneWithOwnerAndGuestsById(Long id);

    @EntityGraph(attributePaths = {"guests", "owner"})
    Optional<Project> findOneWithOwnerAndGuestsByKey(String projectKey);

    @EntityGraph(attributePaths = "guests")
    Optional<Project> findOneWithGuestsByKey(String key);

    List<Project> getProjectsByOwnerOrGuestsContains(User owner, User guest);

    List<Project> getProjectsByOwner(User owner);

    @Named("no_mapstruct")
    default Project getOneByName(String name) {
        return findOneByName(name).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, By.NAME, name));
    }

    @Override
    @Named("no_mapstruct")
    Project getReferenceById(Long aLong);

    Optional<Project> findOneByKey(String key);

    default Project getOneByKey(String key) {
        return findOneByKey(key).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, By.KEY, key));
    }

    Optional<Project> findOneByName(String name);
}
