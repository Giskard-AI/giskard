package ai.giskard.web.rest.controllers;

import ai.giskard.domain.Project;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.web.dto.ml.ProjectDTO;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.NotInDatabaseException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Controller for the {@link Project} resource
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2")
public class ProjectController {
    private final ProjectRepository projectRepository;
    private final ProjectService projectService;
    private final GiskardMapper giskardMapper;

    /**
     * Retrieve the list of projects accessible by the authenticated user
     *
     * @return List of projects
     */
    @GetMapping("project")
    public List<ProjectDTO> list() throws NotInDatabaseException {
        List<Project> projects = projectService.list();
        return giskardMapper.projectsToProjectDTOs(projects);
    }

    /**
     * Update the project with the specified project
     *
     * @param projectDTO project updated to save
     * @param id         id of the existing project
     * @return updated project
     */
    @PreAuthorize("@permissionEvaluator.canWriteProject( #id)")
    @PutMapping(value = "/project/{id}")
    public ProjectDTO updateProject(@RequestBody ProjectPostDTO projectDTO, @PathVariable("id") Long id) {
        Project updatedProject = this.projectService.update(id, projectDTO);
        return giskardMapper.projectToProjectDTO(updatedProject);
    }

    /**
     * Create new project
     *
     * @param projectPostDTO project to save
     * @return created project
     */
    @PostMapping(value = "/project")
    @PreAuthorize("@permissionEvaluator.canWrite()")
    public ProjectDTO create(@RequestBody ProjectPostDTO projectPostDTO, @AuthenticationPrincipal final UserDetails userDetails) {
        Project savedProject = this.projectService.create(projectPostDTO, userDetails);
        return giskardMapper.projectToProjectDTO(savedProject);
    }

    /**
     * Show the specified project
     *
     * @param id id of the project
     * @return created project
     */
    @PreAuthorize("@permissionEvaluator.canReadProject(#id)")
    @GetMapping(value = "/project/{id}")
    @Transactional
    public ProjectDTO show(@PathVariable("id") Long id) {
        Project project = this.projectRepository.getById(id);
        return giskardMapper.projectToProjectDTO(project);
    }

    /**
     * Delete project
     *
     * @param id project's id to delete
     * @return msg Deleted if deleted
     */
    @DeleteMapping(value = "/project/{id}")
    @PreAuthorize("@permissionEvaluator.canWriteProject( #id)")
    public void delete(@PathVariable("id") Long id) {
        this.projectService.delete(id);
    }

    /**
     * Remove user from project's guestlist
     *
     * @param id     project's id
     * @param userId user's id
     * @return updated project
     */
    @DeleteMapping(value = "/project/{id}/guests/{userId}")
    @PreAuthorize("@permissionEvaluator.canWriteProject( #id)")
    public ProjectDTO uninvite(@PathVariable("id") Long id, @PathVariable("userId") Long userId) {
        Project project = this.projectService.uninvite(id, userId);
        return giskardMapper.projectToProjectDTO(project);
    }

    /**
     * Add user to project's guestlist
     *
     * @param id     project's id
     * @param userId user's id
     * @return project updated
     */
    @PreAuthorize("@permissionEvaluator.canWriteProject( #id)")
    @PutMapping(value = "/project/{id}/guests/{userId}")
    public ProjectDTO invite(@PathVariable("id") Long id, @PathVariable("userId") Long userId) {
        Project project = this.projectService.invite(id, userId);
        return giskardMapper.projectToProjectDTO(project);
    }

}
