package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.service.dto.ml.DatasetDTO;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v2/")
public class DatasetsController {

    private DatasetRepository datasetRepository;
    private ProjectRepository projectRepository;
    private UserRepository userRepository;
    private ProjectService projectService;

    public DatasetsController(DatasetRepository datasetRepository, ProjectRepository projectRepository, UserRepository userRepository, ProjectService projectService) {
        this.datasetRepository = datasetRepository;
        this.projectRepository = projectRepository;
        this.userRepository = userRepository;
        this.projectService = projectService;
    }

    /**
     * Retrieve the list of datasets from the specified project
     * Returns all the project's datasets if the user is admin, project's owner or in project's guest list
     *
     * @param projectId id of the project
     * @return List of datasets
     */
    @GetMapping("project/{projectId}/datasets")
    public List<DatasetDTO> listProjectDatasets(@PathVariable @NotNull Long projectId) {
        return this.datasetRepository.findAllByProjectId(projectId).stream().map(DatasetDTO::new).collect(Collectors.toList());
    }
}
