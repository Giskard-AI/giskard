package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.SecurityUtils;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.web.rest.errors.NotInDatabaseException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.Objects;
import java.util.Set;

import static ai.giskard.utils.GiskardStringUtils.toSlug;

@Service
@Transactional
@RequiredArgsConstructor
public class ProjectService {

    final UserRepository userRepository;
    final ProjectRepository projectRepository;
    final GiskardMapper giskardMapper;

    /**
     * Update project
     *
     * @param id         id of the project to update
     * @param projectDTO updated project
     * @return project updated
     */
    public Project update(@NotNull Long id, ProjectPostDTO projectDTO) {
        Project project = projectRepository.getById(id);
        giskardMapper.updateProjectFromDto(projectDTO, project);
        return projectRepository.save(project);
    }

    /**
     * Create project
     *
     * @param project
     * @param ownerLogin
     * @return project saved
     */
    public Project create(Project project, String ownerLogin) {
        String projectKey;
        if (project.getKey() != null) {
            projectKey = toSlug(project.getKey());
        } else {
            projectKey = toSlug(project.getName());
        }
        projectRepository.findOneByKey(projectKey).ifPresent(p -> {
            throw new IllegalArgumentException(String.format("Project with key %s already exists", projectKey));
        });
        project.setKey(projectKey);
        User owner = userRepository.getOneByLogin(ownerLogin);
        project.setOwner(owner);
        return projectRepository.save(project);
    }

    /**
     * Test if the authenticated user is in the guestlist
     *
     * @param userList list of users
     * @return boolean
     */
    public boolean isUserInGuestList(Set<User> userList) {
        return userList.stream().anyMatch(guest -> guest.getLogin().equals(SecurityUtils.getCurrentAuthenticatedUserLogin()));
    }

    /**
     * Delete the project
     *
     * @param id id of the project to delete
     * @return boolean success
     */
    public void delete(Long id) {
        projectRepository.deleteById(id);
    }

    /**
     * Uninvite user from project guestlist
     *
     * @param id     id of the project
     * @param userId id of the user
     * @return update project
     */
    public Project uninvite(Long id, Long userId) {
        User user = userRepository.findById(userId).orElseThrow(() -> new EntityNotFoundException(Entity.USER, userId));
        Project project = projectRepository.findOneWithGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        project.removeGuest(user);
        projectRepository.save(project);
        return project;
    }

    /**
     * Inviting user to the project guestlist
     *
     * @param id     id of the project
     * @param userId id of the user
     * @return updated project
     */
    public Project invite(Long id, Long userId) {
        User user = userRepository.getById(userId);
        Project project = projectRepository.findOneWithGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        project.addGuest(user);
        projectRepository.save(project);
        return project;
    }

    /**
     * Listing projects accessible by the user
     * Handling access control
     *
     * @return list of projects
     */
    public List<Project> list() {
        String username = SecurityUtils.getCurrentAuthenticatedUserLogin().toLowerCase();
        User user = userRepository.findOneByLogin(username).orElseThrow(() -> new NotInDatabaseException(Entity.USER, username));
        List<Project> projects;
        if (SecurityUtils.isCurrentUserAdmin()) {
            projects = projectRepository.findAll();
        } else {
            projects = projectRepository.getProjectsByOwnerOrGuestsContains(user, user);
        }
        return projects;
    }
}
