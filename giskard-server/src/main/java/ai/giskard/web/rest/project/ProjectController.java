package ai.giskard.web.rest.project;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.ProjectService;
import ai.giskard.service.dto.ml.ProjectDTO;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
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
     * @param projectDTO: project updated to save
     * @param id:         id of the existing project
     * @return updated project
     */
    @PutMapping(value = "/project/{id}")
    public ProjectDTO updateProject(@RequestBody ProjectPostDTO projectDTO, @PathVariable("id") Long id, @AuthenticationPrincipal final UserDetails userDetails) {
        this.projectService.accessControlAdminOrOwner(id, userDetails);
        Project updatedProject = this.projectService.update(id, projectDTO);
        return new ProjectDTO(updatedProject);
    }

    /**
     * Create new project
     *
     * @param projectPostDTO: project to save
     * @return created project
     */
    @PostMapping(value = "/project/")
    public ProjectDTO create(@RequestBody ProjectPostDTO projectPostDTO, @AuthenticationPrincipal final UserDetails userDetails) {
        Project savedProject = this.projectService.create(projectPostDTO, userDetails);
        return new ProjectDTO(savedProject);
    }

    /**
     * Show the specified project
     *
     * @param id: id of the project
     * @return created project
     */
    @GetMapping(value = "/project/{id}")
    @Transactional
    public ProjectDTO show(@PathVariable("id") Long id) {
        Project project = this.projectRepository.getById(id);
        return new ProjectDTO(project);
    }

    @DeleteMapping(value = "/project/{id}")
    public boolean delete(@PathVariable("id") Long id, @AuthenticationPrincipal final UserDetails userDetails) {
        this.projectService.accessControlAdminOrOwner(id, userDetails);
        return this.projectService.delete(id);
    }

    /**
     * Remove user from project's guestlist
     *
     * @param id:     project's id
     * @param userId: user's id
     * @return: updated project
     */
    @DeleteMapping(value = "/project/{id}/users/{userId}")
    public ProjectDTO uninvite(@PathVariable("id") Long id, @PathVariable("userId") Long userId, @AuthenticationPrincipal final UserDetails userDetails) {
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
    @PutMapping(value = "/project/{id}/users/{userId}")
    public ProjectDTO invite(@PathVariable("id") Long id, @PathVariable("userId") Long userId, @AuthenticationPrincipal final UserDetails userDetails) {
        this.projectService.accessControlAdminOrOwner(id, userDetails);
        Project project = this.projectService.invite(id, userId);
        return new ProjectDTO(project);
    }

}
