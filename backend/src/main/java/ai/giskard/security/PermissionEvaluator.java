package ai.giskard.security;

import ai.giskard.domain.Project;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

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
     * Determine if a user can write a project, i.e. is admin or project's owner
     *
     * @param id id of the project
     * @return true if the user can write
     */
    public boolean canWriteProject(@NotNull Long id) {
        Project project = this.projectRepository.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        return (isCurrentUser(project.getOwner().getLogin()) || SecurityUtils.isCurrentUserAdmin());
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

}
