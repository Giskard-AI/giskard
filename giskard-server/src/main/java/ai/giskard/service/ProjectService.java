package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.SecurityUtils;
import ai.giskard.service.dto.ml.ProjectDTO;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.service.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.web.rest.errors.NotInDatabaseException;
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
    public ProjectDTO update(@NotNull Long id, ProjectPostDTO projectDTO) {
        Project project = this.projectRepository.getById(id);
        this.giskardMapper.updateProjectFromDto(projectDTO, project);
        Project savedProject = this.projectRepository.save(project);
        return giskardMapper.projectToProjectDTO(savedProject);
    }

    /**
     * Create project
     *
     * @param projectDTO projectDTO to save
     * @return project saved
     */
    public ProjectDTO create(ProjectPostDTO projectDTO, UserDetails userDetails) {
        Project project = this.giskardMapper.projectPostDTOToProject(projectDTO);
        project.setKey(project.getName());
        User owner = this.userRepository.getOneByLogin(userDetails.getUsername());
        project.setOwner(owner);
        return giskardMapper.projectToProjectDTO(this.projectRepository.save(project));
    }

    /**
     * Test if the authenticated user is in the guestlist
     *
     * @param userList list of users
     * @return boolean
     */
    public boolean isUserInGuestList(Set<User> userList) {
        return userList.stream().anyMatch(guest -> guest.getLogin().equals(SecurityUtils.getCurrentUserLogin().get()));
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
    public ProjectDTO uninvite(Long id, Long userId) {
        User user = this.userRepository.findById(userId).orElseThrow(() -> new EntityNotFoundException(Entity.USER, userId));
        Project project = this.projectRepository.findOneWithGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        project.removeGuest(user);
        this.projectRepository.save(project);
        return giskardMapper.projectToProjectDTO(project);
    }


    /**
     * Inviting user to the project guestlist
     *
     * @param id     id of the project
     * @param userId id of the user
     * @return updated project
     */
    public ProjectDTO invite(Long id, Long userId) {
        User user = this.userRepository.getById(userId);
        Project project = this.projectRepository.findOneWithGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        project.addGuest(user);
        this.projectRepository.save(project);
        return giskardMapper.projectToProjectDTO(project);
    }

    /**
     * Listing projects accessible by the user
     * Handling access control
     *
     * @return list of projects
     */
    public List<ProjectDTO> list() {
        String username = SecurityUtils.getCurrentUserLogin().get().toLowerCase();
        User user = userRepository.findOneByLogin(username).orElseThrow(() -> new NotInDatabaseException(Entity.USER, username));
        List<Project> projects;
        if (SecurityUtils.isAdmin()) {
            projects = projectRepository.findAll();
        } else {
            projects = projectRepository.getProjectsByOwnerOrGuestsContains(user, user);
        }
        return giskardMapper.projectsToProjectDTOs(projects);
    }
}
