package ai.giskard.security;

import ai.giskard.domain.Project;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.web.rest.errors.EntityAccessControlException;
import ai.giskard.web.rest.errors.UnauthorizedException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.PermissionEvaluator;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.validation.constraints.NotNull;
import java.io.Serializable;

import static ai.giskard.security.SecurityUtils.hasCurrentUserAnyOfAuthorities;

@Component(value = "permissionEvaluator")
public class PermissionEvaluatorImpl implements PermissionEvaluator {
    //public PermissionEvaluatorImpl() {}
    @Autowired
    ProjectRepository projectRepository;

    @Autowired
    UserRepository userRepository;
    @Autowired
    ProjectService projectService;

    public boolean isCurrentUser(String login) {
        return login.equals(SecurityUtils.getCurrentUserLogin().get());
    }

    /**
     * Determine if a user can write a project, i.e. is admin or project's owner
     *
     * @param id: id of the project
     * @return: true if the user can write
     */
    public boolean canWriteProject(@NotNull Long id) {
        boolean isAdmin = SecurityUtils.hasCurrentUserThisAuthority(AuthoritiesConstants.ADMIN);
        Project project = this.projectRepository.getById(id);
        return (isCurrentUser(project.getOwner().getLogin()) || isAdmin);
    }

    /**
     * Determine if a user can write, ie has AICreator or Admin authorities
     */
    public boolean canWrite() {
        String[] writeAuthorities = {AuthoritiesConstants.AICREATOR, AuthoritiesConstants.ADMIN};
        return hasCurrentUserAnyOfAuthorities(writeAuthorities);
    }

    /**
     * Determine if the user can read the project, is admin, in project's guestlist or project's owner
     *
     * @param id: project's id
     * @return: true if user can read
     */
    public boolean canReadProject(@NotNull Long id) {
        boolean isAdmin = SecurityUtils.hasCurrentUserThisAuthority(AuthoritiesConstants.ADMIN);
        Project project = this.projectRepository.getOneWithGuestsById(id);
        return (projectService.isUserInGuestList(project.getGuests()) || isCurrentUser(project.getOwner().getLogin()) || isAdmin);
    }

    @Override
    public boolean hasPermission(Authentication authentication, Object targetDomainObject, Object permission) {
        return false;
    }

    @Override
    public boolean hasPermission(Authentication authentication, Serializable targetId, String targetType, Object permission) {
        return false;
    }
}
