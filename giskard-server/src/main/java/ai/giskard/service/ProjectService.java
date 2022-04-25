package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.SecurityUtils;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.service.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.EntityAccessControlException;
import ai.giskard.web.rest.errors.UnauthorizedException;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.validation.constraints.NotNull;
import java.util.Arrays;
import java.util.List;
import java.util.Set;

import static ai.giskard.security.SecurityUtils.hasCurrentUserAnyOfAuthorities;

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
     * Test if the specified name is the connected user
     *
     * @param login: specified login to test
     * @return: true if login match the current user
     */
    public boolean isCurrentUser(String login) {
        return login.equals(SecurityUtils.getCurrentUserLogin().get());
    }

    /**
     * Test if the authenticated user is in the guestlist
     *
     * @param userList: list of users
     * @return: boolean
     */
    public boolean isUserInGuestList(Set<User> userList) {
        return userList.stream().anyMatch(guest -> guest.getLogin() == SecurityUtils.getCurrentUserLogin().get());
    }

    /**
     * Managing access control for specified project
     * Accessing if project's owner, in project's guestlist or admin
     * TODO: move it to permission
     *
     * @param projectId: id of the project
     * @throws EntityAccessControlException
     */
    public void accessControlRead(@NotNull Long projectId) throws EntityAccessControlException {
        boolean isAdmin = SecurityUtils.hasCurrentUserThisAuthority(AuthoritiesConstants.ADMIN);
        Project project = this.projectRepository.getOneWithGuestsById(projectId);
        if (!isUserInGuestList(project.getGuests()) && isCurrentUser(project.getOwner().getLogin()) && !isAdmin) {
            throw new EntityAccessControlException(EntityAccessControlException.Entity.PROJECT, projectId);
        }
    }


    /**
     * Giving access only for admin and project owner for specified project
     * TODO: move it to permission
     *
     * @param projectId: id of the project
     * @throws EntityAccessControlException
     */
    public void accessControlWrite(@NotNull Long projectId) throws EntityAccessControlException {
        boolean isAdmin = SecurityUtils.hasCurrentUserThisAuthority(AuthoritiesConstants.ADMIN);
        Project project = this.projectRepository.getById(projectId);
        if (!isCurrentUser(project.getOwner().getLogin()) && !isAdmin) {
            throw new EntityAccessControlException(EntityAccessControlException.Entity.PROJECT, projectId);
        }
    }

    /**
     * Giving access only for admin and aicreator
     * TODO: move it to permission
     *
     * @throws EntityAccessControlException
     */
    public void accessControlWrite() throws UnauthorizedException {
        String[] writeAuthorities = {AuthoritiesConstants.AICREATOR, AuthoritiesConstants.ADMIN};
        boolean isAdminOrCreator = hasCurrentUserAnyOfAuthorities(writeAuthorities);
        if (!isAdminOrCreator) {
            throw new UnauthorizedException("CREATION", UnauthorizedException.Entity.PROJECT);
        }
    }


    /**
     * Delete the project
     *
     * @param id: id of the project to delete
     * @return: boolean success
     */
    public boolean delete(Long id) {
        accessControlWrite(id);
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
        accessControlWrite(id);
        User user = this.userRepository.getById(userId);
        Project project = this.projectRepository.getOneWithGuestsById(id);
        project.removeGuest(user);
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
        accessControlWrite(id);
        User user = this.userRepository.getById(userId);
        Project project = this.projectRepository.getOneWithGuestsById(id);
        project.addGuest(user);
        this.projectRepository.save(project);
        return project;
    }

}
