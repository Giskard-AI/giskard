package ai.giskard.web.temp;

import ai.giskard.domain.Project;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.web.dto.ml.ProjectDTO;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

/**
 * Test Controller for the {@link Project} resource
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2")
public class TestProjectController {
    private final TestGiskardMapper testGiskardMapper;
    private final ProjectRepository projectRepository;

    /**
     * Update the project with the specified project
     *
     * @param projectDTO project updated to save
     * @param id         id of the existing project
     * @return updated project
     */
    @PutMapping(value = "/_project/{id}")
    public ProjectDTO updateProject(@RequestBody TestProjectPostDTO projectDTO, @PathVariable("id") Long id) {
        Project project = projectRepository.getById(id);
        testGiskardMapper.updateProjectFromDto(projectDTO, project);
        Project updatedProject= projectRepository.save(project);
        return testGiskardMapper.projectToProjectDTO(updatedProject);
    }

    /**
     * Update the project with the specified project
     *
     * @param projectDTO project updated to save
     * @param id         id of the existing project
     * @return updated project
     */
    @PutMapping(value = "/_project_t/{id}")
    @Transactional
    public ProjectDTO updateProjectTransactional(@RequestBody TestProjectPostDTO projectDTO, @PathVariable("id") Long id) {
        Project project = projectRepository.getById(id);
        testGiskardMapper.updateProjectFromDto(projectDTO, project);
        Project updatedProject= projectRepository.save(project);
        return testGiskardMapper.projectToProjectDTO(updatedProject);
    }
//
//    /**
//     * Create new project
//     *
//     * @param projectPostDTO project to save
//     * @return created project
//     */
//    @PostMapping(value = "/_project")
//    public ProjectDTO create(@RequestBody ProjectPostDTO projectPostDTO, @AuthenticationPrincipal final UserDetails userDetails) {
//        Project savedProject = this.projectService.create(projectPostDTO, userDetails);
//        return testGiskardMapper.projectToProjectDTO(savedProject);
//    }
}
