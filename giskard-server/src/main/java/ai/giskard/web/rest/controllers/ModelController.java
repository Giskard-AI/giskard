package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.web.dto.ModelMetadataDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.ModelDTO;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class ModelController {
    private final ModelRepository modelRepository;
    private final GiskardMapper giskardMapper;
    private final PermissionEvaluator permissionEvaluator;
    private final Logger log = LoggerFactory.getLogger(ModelController.class);


    /**
     * Retrieve the list of models from the specified project
     * Returns all the project's models if the user is admin, project's owner or in project's guest list
     *
     * @param projectId id of the project
     * @return List of models
     */
    @GetMapping("project/{projectId}/models")
    public List<ModelDTO> listProjectModels(@PathVariable @NotNull Long projectId) {
        return giskardMapper.modelsToModelDTOs(modelRepository.findAllByProjectId(projectId));
    }

    @GetMapping("model/{modelId}/metadata")
    @Transactional
    public ModelMetadataDTO getModelMetadata(@PathVariable @NotNull Long modelId){
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        return giskardMapper.modelToModelMetadataDTO(model);
    }

}
