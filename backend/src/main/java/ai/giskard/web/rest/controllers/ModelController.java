package ai.giskard.web.rest.controllers;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ModelType;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.dto.MLWorkerWSExplainDTO;
import ai.giskard.ml.dto.MLWorkerWSExplainTextDTO;
import ai.giskard.ml.dto.MLWorkerWSRunModelForDataFrameDTO;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.ModelService;
import ai.giskard.service.ProjectFileDeletionService;
import ai.giskard.service.UsageService;
import ai.giskard.service.ee.LicenseException;
import ai.giskard.service.ee.LicenseService;
import ai.giskard.web.dto.*;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class ModelController {
    private final Logger log = LoggerFactory.getLogger(ModelController.class);
    private final ModelRepository modelRepository;
    private final DatasetRepository datasetRepository;
    private final ProjectRepository projectRepository;
    private final UsageService usageService;
    private final GiskardMapper giskardMapper;
    private final PermissionEvaluator permissionEvaluator;
    private final ModelService modelService;
    private final ProjectFileDeletionService deletionService;
    private final LicenseService licenseService;


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

    @PostMapping("models/{modelId}/explain/{datasetId}")
    public ExplainResponseDTO explain(@PathVariable @NotNull UUID modelId, @PathVariable @NotNull UUID datasetId, @RequestBody @NotNull PredictionInputDTO data) {
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        MLWorkerWSExplainDTO explanations = modelService.explain(model, dataset, data.getFeatures());
        ExplainResponseDTO result = new ExplainResponseDTO();
        if (explanations != null) {
            explanations.getExplanations().forEach((label, perFeatureExplanations) ->
                result.getExplanations().put(label, perFeatureExplanations.getPerFeature()));
        }
        return result;
    }


    @GetMapping("project/{projectKey}/models/{modelId}")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public ModelDTO getModelMeta(@PathVariable("projectKey") @NotNull String projectKey,
                                 @PathVariable("modelId") @NotNull UUID modelId) {
        return giskardMapper.modelToModelDTO(modelRepository.getMandatoryById(modelId));
    }

    @PostMapping("project/{projectKey}/models")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public void createModelMeta(@PathVariable("projectKey") @NotNull String projectKey, @RequestBody @NotNull ModelDTO dto) {
        if (modelRepository.existsById(dto.getId())) {
            log.info("Model already exists {}", dto.getId());
            return;
        }
        Project project = projectRepository.getOneByKey(projectKey);
        Integer modelPerProject = licenseService.getCurrentLicense().getModelPerProjectLimit();
        if (modelPerProject != null && project.getModels().size() >= modelPerProject) {
            log.info("Exceed model numbers in project '{}'", project.getName());
            // Improve the statement
            throw new LicenseException(
                "You've reached your limit of " +
                    licenseService.getCurrentLicense().getModelPerProjectLimit() +
                    " models per project allowed by the " +
                    licenseService.getCurrentLicense().getPlanName() +
                    " plan. " +
                "Please upgrade your license to keep more versions."
            );
        }
        ProjectModel model = giskardMapper.fromDTO(dto);
        model.setProject(project);
        modelRepository.save(model);
    }


    @PostMapping("models/explain-text/{featureName}")
    public ExplainTextResponseDTO explainText(@RequestParam @NotNull UUID modelId, @RequestParam @NotNull UUID datasetId, @PathVariable @NotNull String featureName, @RequestBody @NotNull PredictionInputDTO data) {
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        ExplainTextResponseDTO explanationRes = new ExplainTextResponseDTO();
        MLWorkerWSExplainTextDTO textResponse = modelService.explainText(model, dataset, featureName, data.getFeatures());
        textResponse.getWeights().forEach((label, weightPerFeature) ->
            explanationRes.getWeights().put(label, weightPerFeature.getWeights())
        );
        explanationRes.setWords(textResponse.getWords());
        return explanationRes;
    }

    @DeleteMapping("models/{modelId}")
    public MessageDTO deleteModel(@PathVariable @NotNull UUID modelId) {
        deletionService.deleteModel(modelId);
        return new MessageDTO("Model {} has been deleted", modelId);
    }

    @PostMapping("models/{modelId}/predict")
    public PredictionDTO predict(@PathVariable @NotNull UUID modelId,
                                 @RequestBody @NotNull PredictionInputDTO data) {
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(data.getDatasetId());
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        MLWorkerWSRunModelForDataFrameDTO result = modelService.predict(model, dataset, data.getFeatures());
        Map<String, Float> allPredictions = new HashMap<>();
        if (model.getModelType() == ModelType.CLASSIFICATION) {
            result.getAllPredictions().getRows().get(0).getColumns().forEach((label, proba) ->
                allPredictions.put(label, Float.parseFloat(proba))
            );
        }
        return new PredictionDTO(result.getPrediction().get(0), allPredictions);
    }

    @GetMapping("models/prepare-delete/{modelId}")
    public PrepareDeleteDTO prepareModelDelete(@PathVariable @NotNull UUID modelId) {
        return usageService.prepareDeleteModel(modelId);
    }

    @PatchMapping("models/{modelId}/name/{name}")
    public ModelDTO renameModel(@PathVariable UUID modelId, @PathVariable @Valid @NotBlank String name) {
        ProjectModel model = modelRepository.findById(modelId)
            .orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT_MODEL, modelId.toString()));

        permissionEvaluator.validateCanWriteProject(model.getProject().getId());

        model.setName(name);

        return giskardMapper.modelToModelDTO(modelRepository.save(model));
    }

}
