package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.web.rest.errors.EntityAccessControlException;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.validation.constraints.NotNull;

@Service
@Transactional
public class ProjectService {
    private static final org.slf4j.Logger logger = LoggerFactory.getLogger(ProjectService.class);

    UserRepository userRepository;
    ProjectRepository projectRepository;

    public ProjectService(UserRepository userRepository, ProjectRepository projectRepository) {
        this.userRepository = userRepository;
        this.projectRepository = projectRepository;
    }

    /**
     * Update project
     *
     * @param id:             id of the project to update
     * @param updatedProject: updated project
     * @return: project updated
     */
    public Project update(@NotNull Long id, Project updatedProject) {
        Project project = this.projectRepository.getById(id);
        project.setName(updatedProject.getName());
        project.setDatasets(updatedProject.getDatasets());
        project.setDescription(updatedProject.getDescription());
        project.setLocalDateTime(updatedProject.getLocalDateTime());
        project.setOwner(updatedProject.getOwner());
        project.setUsers(updatedProject.getUsers());
        project.setModels(updatedProject.getModels());
        this.projectRepository.save(project);
        return project;
    }

    /**
     * Create project
     *
     * @param updatedProject: updated project
     * @return: project saved
     */
    public Project create(Project updatedProject) {
        Project project = new Project();
        project.setName(updatedProject.getName());
        project.setDatasets(updatedProject.getDatasets());
        project.setDescription(updatedProject.getDescription());
        project.setLocalDateTime(updatedProject.getLocalDateTime());
        project.setOwner(updatedProject.getOwner());
        project.setUsers(updatedProject.getUsers());
        project.setModels(updatedProject.getModels());
        this.projectRepository.save(project);
        return project;
    }

    /**
     * Managing access control for specified project
     * TODO: move it to permission
     *
     * @param projectId:   id of the project
     * @param userDetails: user details
     * @throws EntityAccessControlException
     */
    public void accessControlById(@NotNull Long projectId, UserDetails userDetails) throws EntityAccessControlException {
        boolean isAdmin = userDetails.getAuthorities().stream().anyMatch(authority -> authority.getAuthority() == AuthoritiesConstants.ADMIN);
        User user = userRepository.getOneWithProjectsByLogin(userDetails.getUsername());
        Project project = this.projectRepository.getOneWithUsersById(projectId);
        boolean isUserInGuestListProject = project.getUsers().contains(user);
        if (!isUserInGuestListProject && project.getOwner() != user && !isAdmin) {
            throw new EntityAccessControlException(EntityAccessControlException.Entity.PROJECT, projectId);
        }
    }

    /**
     * Giving access only for admin and project owner for specified project
     * TODO: move it to permission
     *
     * @param projectId:   id of the project
     * @param userDetails: user details
     * @throws EntityAccessControlException
     */
    public void accessControlAdminOrOwner(@NotNull Long projectId, UserDetails userDetails) throws EntityAccessControlException {
        boolean isAdmin = userDetails.getAuthorities().stream().anyMatch(authority -> authority.getAuthority() == AuthoritiesConstants.ADMIN);
        User user = userRepository.getOneByLogin(userDetails.getUsername());
        Project project = this.projectRepository.getById(projectId);
        if (project.getOwner() != user && !isAdmin) {
            throw new EntityAccessControlException(EntityAccessControlException.Entity.PROJECT, projectId);
        }
    }
    

    /**
     * Delete the project
     *
     * @param project: project to delete
     * @return: boolean success
     */
    public boolean delete(Project project) {
        this.projectRepository.delete(project);
        this.projectRepository.flush();
        return true;
    }

    /**
     * Uninvite user from project guestlist
     *
     * @param id:     id of the project
     * @param userId: id of the user
     * @return update project
     */
    public Project uninvite(Long id, Long userId) {
        User user = this.userRepository.getById(userId);
        Project project = this.projectRepository.getOneWithUsersById(id);
        project.removeUser(user);
        this.projectRepository.save(project);
        return project;
    }

    /**
     * Inviting user to the project guestlist
     *
     * @param id:     id of the project
     * @param userId: id of the user
     * @return updated project
     */
    public Project invite(Long id, Long userId) {
        User user = this.userRepository.getById(userId);
        Project project = this.projectRepository.getOneWithUsersById(id);
        project.addUser(user);
        this.projectRepository.save(project);
        return project;
    }

}
