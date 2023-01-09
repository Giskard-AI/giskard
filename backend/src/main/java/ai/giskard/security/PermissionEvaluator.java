package ai.giskard.security;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

import static ai.giskard.security.SecurityUtils.hasCurrentUserAnyOfAuthorities;

@Component(value = "permissionEvaluator")
@RequiredArgsConstructor
public class PermissionEvaluator {
    final ProjectRepository projectRepository;

    final ProjectService projectService;

    public boolean isCurrentUser(String login) {
        return login.equals(SecurityUtils.getCurrentAuthenticatedUserLogin());
    }

    /**
     * Determine if a user can write a project, i.e. is admin, is project's owner or is guest with any role
     *
     * @param id    id of the project
     * @param roles list of roles that guests need to have in order to be able to write (if empty guests cannot write)
     * @return true if the user can write
     */
    public boolean canWriteProject(@NotNull Long id, @NotBlank String... roles) {
        Project project = this.projectRepository.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));

        return isCurrentUser(project.getOwner().getLogin())
            || SecurityUtils.isCurrentUserAdmin()
            || (roles.length > 0 && SecurityUtils.hasCurrentUserAnyOfAuthorities(roles) && isCurrentUserGuest(project));
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
     * @param id project's id
     * @return true if user can read
     */
    @Transactional
    public boolean canReadProject(@NotNull Long id) {
        Project project = this.projectRepository.findOneWithGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        return (projectService.isUserInGuestList(project.getGuests()) || isCurrentUser(project.getOwner().getLogin()) || SecurityUtils.isCurrentUserAdmin());
    }

    @Transactional
    public void validateCanReadProject(@NotNull Long id) {
        if (!canReadProject(id)) {
            throw new AccessDeniedException("Access denied to project id " + id);
        }
    }

    @Transactional
    public void validateCanWriteProject(@NotNull Long id) {
        if (!canWriteProject(id)) {
            throw new AccessDeniedException("Access denied to project id " + id);
        }
    }

    /**
     * Check if current user is a guest for the project
     *
     * @param project The project to check guests from
     * @return true when current user is inside the guests of the project, false otherwise
     */
    private boolean isCurrentUserGuest(Project project) {
        return project.getGuests().stream()
            .map(User::getLogin)
            .anyMatch(this::isCurrentUser);
    }

}
