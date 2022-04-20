package ai.giskard.web.rest.project;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.ProjectService;
import ai.giskard.service.dto.ml.ModelDTO;
import ai.giskard.service.dto.ml.ProjectDTO;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v2")
public class ProjectController {
    private final ProjectRepository projectRepository;
    private final UserRepository userRepository;
    private final ProjectService projectService;

    public ProjectController(ProjectRepository projectRepository, UserRepository userRepository, ProjectService projectService) {
        this.projectRepository = projectRepository;
        this.userRepository = userRepository;
        this.projectService = projectService;
    }

    /**
     * Retrieve the list of projects accessible by the authenticated user
     *
     * @param userDetails: authenticated user's details
     * @return: List of projects
     */
    @GetMapping("project")
    public List<ProjectDTO> list(@AuthenticationPrincipal final UserDetails userDetails) {
        boolean isAdmin = userDetails.getAuthorities().stream().anyMatch(authority -> authority.getAuthority() == AuthoritiesConstants.ADMIN);
        List<Project> projects;
        if (isAdmin) {
            projects = projectRepository.findAll();
        } else {
            User user = userRepository.getOneWithProjectsByLogin(userDetails.getUsername());
            projects = user.getProjects();
        }
        return projects.stream().map(ProjectDTO::new).collect(Collectors.toList());

    }
}
