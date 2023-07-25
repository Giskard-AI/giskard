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
     * Determine if a user can write a project, i.e. is admin or is project's owner
     *
     * @param id id of the project
     * @return true if the user can write
     */
    public boolean canWriteProject(@NotNull Long id) {
        Project project = this.projectRepository.getMandatoryById(id);

        return isCurrentUser(project.getOwner().getLogin()) || SecurityUtils.isCurrentUserAdmin();
    }

    /**
     * Determine if the current user is a guest of a project and is granted any of the required roles
     *
     * @param projectId id of the project
     * @param roles     list of roles that guests need to have in order to be able to write
     * @return true if the user is guest with the required permissions
     */
    public boolean isGuestWithAnyRole(@NotNull Long projectId, @NotBlank String... roles) {
        Project project = this.projectRepository.getMandatoryById(projectId);

        return SecurityUtils.hasCurrentUserAnyOfAuthorities(roles) && isCurrentUserGuest(project);
    }

    public boolean canWriteProjectKey(@NotNull String projectKey) {
        Project project = this.projectRepository.findOneByKey(projectKey)
            .orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, projectKey));

        if (isCurrentUserGuest(project) && isGuestWithAnyRole(project.getId(), AuthoritiesConstants.AICREATOR, AuthoritiesConstants.ADMIN)) {
            return true;
        }

        return isCurrentUser(project.getOwner().getLogin()) || SecurityUtils.isCurrentUserAdmin();
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
    public boolean canReadProject(@NotNull Long id) {
        Project project = this.projectRepository.findOneWithOwnerAndGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        return (projectService.isUserInGuestList(project.getGuests()) || isCurrentUser(project.getOwner().getLogin()) || SecurityUtils.isCurrentUserAdmin());
    }

    public boolean canReadProjectKey(@NotNull String projectKey) {
        Project project = this.projectRepository.findOneWithOwnerAndGuestsByKey(projectKey).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, projectKey));
        return (projectService.isUserInGuestList(project.getGuests()) || isCurrentUser(project.getOwner().getLogin()) || SecurityUtils.isCurrentUserAdmin());
    }

    public void validateCanReadProject(@NotNull Long id) {
        if (!canReadProject(id)) {
            throw new AccessDeniedException("Access denied to project id " + id);
        }
    }

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
