package ai.giskard.repository;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ProjectRepository extends JpaRepository<Project, Long> {

    @EntityGraph(attributePaths = "guests")
    Project getOneWithGuestsById(Long id);

    List<Project> getProjectsByOwnerOrGuestsContains(User owner, User guest);

    Project getOneByOwner_Login(String login);

    Project getOneByName(String name);



    Optional<Project> findOneByName(String name);


}
