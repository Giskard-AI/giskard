package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.SecurityUtils;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.service.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.NotInDatabaseException;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.Set;

@Service
@Transactional
public class ProjectService {

    UserRepository userRepository;
    ProjectRepository projectRepository;
    GiskardMapper giskardMapper;

    public ProjectService(UserRepository userRepository, ProjectRepository projectRepository, GiskardMapper giskardMapper) {
        this.userRepository = userRepository;
        this.projectRepository = projectRepository;
        this.giskardMapper = giskardMapper;
    }

    /**
     * Update project
     *
     * @param id         id of the project to update
     * @param projectDTO updated project
     * @return project updated
     */
    @Transactional
    public Project update(@NotNull Long id, ProjectPostDTO projectDTO) {
        Project project = this.projectRepository.getById(id);
        this.giskardMapper.updateProjectFromDto(projectDTO, project);
        Project savedProject = this.projectRepository.save(project);
        return savedProject;
    }

    /**
     * Create project
     *
     * @param projectDTO projectDTO to save
     * @return project saved
     */
    public Project create(ProjectPostDTO projectDTO, @AuthenticationPrincipal final UserDetails userDetails) {
        Project project = this.giskardMapper.projectPostDTOToProject(projectDTO);
        User owner = this.userRepository.getOneByLogin(userDetails.getUsername());
        project.setOwner(owner);
        return this.projectRepository.save(project);
    }

    /**
     * Test if the authenticated user is in the guestlist
     *
     * @param userList list of users
     * @return boolean
     */
    public boolean isUserInGuestList(Set<User> userList) {
        return userList.stream().anyMatch(guest -> guest.getLogin() == SecurityUtils.getCurrentUserLogin().get());
    }

    /**
     * Delete the project
     *
     * @param id id of the project to delete
     * @return boolean success
     */
    public boolean delete(Long id) {
        this.projectRepository.deleteById(id);
        return true;
    }

    /**
     * Uninvite user from project guestlist
     *
     * @param id     id of the project
     * @param userId id of the user
     * @return update project
     */
    public Project uninvite(Long id, Long userId) {
        User user = this.userRepository.getById(userId);
        Project project = this.projectRepository.getOneWithGuestsById(id);
        project.removeGuest(user);
        this.projectRepository.save(project);
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
        User user = this.userRepository.getById(userId);
        Project project = this.projectRepository.getOneWithGuestsById(id);
        project.addGuest(user);
        this.projectRepository.save(project);
        return project;
    }

    /**
     * Listing projects accessible by the user
     * Handling access control
     *
     * @return list of projects
     */
    public List<Project> list() {
        boolean isAdmin = SecurityUtils.hasCurrentUserThisAuthority(AuthoritiesConstants.ADMIN);
        String username = SecurityUtils.getCurrentUserLogin().get().toLowerCase();
        User user = userRepository.getOneByLogin(username);
        if (user == null) {
            throw new NotInDatabaseException(NotInDatabaseException.Entity.USER, username);
        }
        List<Project> projects;
        if (isAdmin) {
            projects = projectRepository.findAll();
        } else {
            projects = projectRepository.getProjectsByOwnerOrGuestsContains(user, user);
        }
        return projects;
    }
}
