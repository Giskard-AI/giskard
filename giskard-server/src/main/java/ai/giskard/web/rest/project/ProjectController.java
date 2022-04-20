package ai.giskard.web.rest.project;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.ProjectService;
import ai.giskard.service.dto.ml.ProjectDTO;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

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

    /**
     * Update the project with the specified project
     *
     * @param project: project updated to save
     * @param id:      id of the existing project
     * @return updated project
     */
    @PutMapping(value = "/project/{id}")
    public ProjectDTO updatePerson(@RequestBody Project project, @PathVariable("id") Long id, @AuthenticationPrincipal final UserDetails userDetails) {
        this.projectService.accessControlAdminOrOwner(id, userDetails);
        return new ProjectDTO(this.projectService.update(id, project));
    }

    /**
     * Create new project
     *
     * @param project: project to save
     * @return created project
     */
    @PostMapping(value = "/project/")
    public ProjectDTO create(@RequestBody Project project, @AuthenticationPrincipal final UserDetails userDetails) {
        boolean isAdmin = userDetails.getAuthorities().stream().anyMatch(authority -> authority.getAuthority() == AuthoritiesConstants.ADMIN);
        return new ProjectDTO(this.projectService.create(project));
    }

    /**
     * Show the specified project
     *
     * @param id: id of the project
     * @return created project
     */
    @GetMapping(value = "/project/{id}")
    public ProjectDTO show(@PathVariable("id") Long id) {
        return new ProjectDTO(this.projectRepository.getById(id));
    }

    @DeleteMapping(value = "/project/{id}")
    private boolean delete(Project project, @AuthenticationPrincipal final UserDetails userDetails) {
        this.projectService.accessControlAdminOrOwner(project.getId(), userDetails);
        return this.projectService.delete(project);
    }

    /**
     * Remove user from project's guestlist
     *
     * @param id:     project's id
     * @param userId: user's id
     * @return: updated project
     */
    @PutMapping(value = "/project/{id}/uninvite")
    public ProjectDTO uninvite(@PathVariable("id") Long id, @RequestBody Long userId, @AuthenticationPrincipal final UserDetails userDetails) {
        this.projectService.accessControlAdminOrOwner(id, userDetails);
        Project project = this.projectService.uninvite(id, userId);
        return new ProjectDTO(project);
    }

    /**
     * Add user to project's guestlist
     *
     * @param id:     project's id
     * @param userId: user's id
     * @return project updated
     */
    @PutMapping(value = "/project/{id}/invite")
    public ProjectDTO invite(@PathVariable("id") Long id, @RequestBody Long userId,@AuthenticationPrincipal final UserDetails userDetails) {
        this.projectService.accessControlAdminOrOwner(id, userDetails);
        Project project = this.projectService.invite(id, userId);
        return new ProjectDTO(project);
    }

}
