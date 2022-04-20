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

    public void accessControlById(@NotNull Long projectId, UserDetails userDetails) throws EntityAccessControlException {
        boolean isAdmin = userDetails.getAuthorities().stream().anyMatch(authority -> authority.getAuthority() == AuthoritiesConstants.ADMIN);
        User user = userRepository.getOneWithProjectsByLogin(userDetails.getUsername());
        Project project = this.projectRepository.getOneWithUsersById(projectId);
        boolean isUserInGuestListProject = project.getUsers().contains(user);
        if (!isUserInGuestListProject && project.getOwner() != user && !isAdmin) {
            throw new EntityAccessControlException(EntityAccessControlException.Entity.PROJECT, projectId);
        }
    }

}
