package ai.giskard.repository;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ProjectRepository extends JpaRepository<Project, Long> {

    @EntityGraph(attributePaths = "users")
    Project getOneWithUsersById(Long id);

    List<Project> getProjectsByOwnerOrGuestsContains(User owner, User guest);

    Project getOneByOwner_Login(String login);

}
