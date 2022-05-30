package ai.giskard.repository;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ProjectRepository extends MappableJpaRepository<Project, Long> {
    @EntityGraph(attributePaths = "guests")
    Optional<Project> findOneWithGuestsById(Long id);

    List<Project> getProjectsByOwnerOrGuestsContains(User owner, User guest);

    Project getOneByName(String name);

    Project getOneByKey(String key);

    Optional<Project> findOneByName(String name);
}
