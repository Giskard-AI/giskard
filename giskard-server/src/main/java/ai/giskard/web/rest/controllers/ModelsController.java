package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.service.dto.ml.ModelDTO;
import ai.giskard.service.mapper.GiskardMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;

@RestController
@RequestMapping("/api/v2/")
public class ModelsController {
    private ModelRepository modelRepository;
    private GiskardMapper giskardMapper;

    public ModelsController(ModelRepository modelRepository, GiskardMapper giskardMapper) {
        this.modelRepository = modelRepository;
        this.giskardMapper = giskardMapper;
    }

    /**
     * Retrieve the list of models from the specified project
     * Returns all the project's models if the user is admin, project's owner or in project's guest list
     *
     * @param projectId id of the project
     * @return List of models
     */
    @GetMapping("project/{projectId}/models")
    public List<ModelDTO> listProjectModels(@PathVariable @NotNull Long projectId) {
        return this.giskardMapper.modelsToModelDTOs(modelRepository.findAllByProjectId(projectId));
    }

}
