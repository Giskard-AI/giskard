package ai.giskard.web.rest.controllers;

import ai.giskard.domain.Project;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.service.dto.ml.ProjectDTO;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.service.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.NotInDatabaseException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v2")
public class ProjectController {
    private final ProjectRepository projectRepository;
    private final ProjectService projectService;
    private final GiskardMapper giskardMapper;

    public ProjectController(ProjectRepository projectRepository, ProjectService projectService, GiskardMapper giskardMapper) {
        this.projectRepository = projectRepository;
        this.projectService = projectService;
        this.giskardMapper = giskardMapper;
    }

    /**
     * Retrieve the list of projects accessible by the authenticated user
     *
     * @return List of projects
     */
    @GetMapping("project")
    public List<ProjectDTO> list() throws NotInDatabaseException {
        List<ProjectDTO> projectDTOs = projectService.list();
        return projectDTOs;
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
        ProjectDTO updatedProjectDTO = this.projectService.update(id, projectDTO);
        return updatedProjectDTO;
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
        ProjectDTO savedProject = this.projectService.create(projectPostDTO, userDetails);
        return savedProject;
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
     * @return true if success
     */
    @DeleteMapping(value = "/project/{id}")
    @PreAuthorize("@permissionEvaluator.canWriteProject( #id)")
    public boolean delete(@PathVariable("id") Long id) {
        return this.projectService.delete(id);
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
        ProjectDTO projectDTO = this.projectService.uninvite(id, userId);
        return projectDTO;
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
        ProjectDTO projectDTO = this.projectService.invite(id, userId);
        return projectDTO;
    }

}
