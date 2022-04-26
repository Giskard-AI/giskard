package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.service.ProjectService;
import ai.giskard.service.dto.ml.ModelDTO;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v2/")
public class ModelsController {
    private ModelRepository modelRepository;
    private final ProjectRepository projectRepository;
    private final UserRepository userRepository;
    private final ProjectService projectService;

    public ModelsController(ModelRepository modelRepository, ProjectRepository projectRepository, UserRepository userRepository, ProjectService projectService) {
        this.modelRepository = modelRepository;
        this.projectRepository = projectRepository;
        this.userRepository = userRepository;
        this.projectService = projectService;
    }

    /**
     * Retrieve the list of models from the specified project
     * Returns all the project's models if the user is admin, project's owner or in project's guest list
     *
     * @param projectId     id of the project
     * @return List of models
     */
    @GetMapping("project/{projectId}/models")
    public List<ModelDTO> listProjectModels(@PathVariable @NotNull Long projectId) {
        return this.modelRepository.findAllByProjectId(projectId).stream().map(ModelDTO::new).collect(Collectors.toList());
    }

}
