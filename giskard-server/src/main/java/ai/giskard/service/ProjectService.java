package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.service.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.EntityAccessControlException;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
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
    GiskardMapper giskardMapper;

    public ProjectService(UserRepository userRepository, ProjectRepository projectRepository, GiskardMapper giskardMapper) {
        this.userRepository = userRepository;
        this.projectRepository = projectRepository;
        this.giskardMapper = giskardMapper;
    }

    /**
     * Update project
     *
     * @param id:         id of the project to update
     * @param projectDTO: updated project
     * @return: project updated
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
     * @param projectDTO: projectDTO to save
     * @return: project saved
     */
    public Project create(ProjectPostDTO projectDTO, @AuthenticationPrincipal final UserDetails userDetails) {
        Project project = this.giskardMapper.projectPostDTOToProject(projectDTO);
        User owner = this.userRepository.getOneByLogin(userDetails.getUsername());
        project.setOwner(owner);
        return this.projectRepository.save(project);
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
     * @param id: id of the project to delete
     * @return: boolean success
     */
    public boolean delete(Long id) {
        this.projectRepository.deleteById(id);
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
