package ai.giskard.web.rest.controllers;

import ai.giskard.domain.InspectionSettings;
import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ModelType;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.ModelService;
import ai.giskard.service.ProjectFileDeletionService;
import ai.giskard.service.UsageService;
import ai.giskard.web.dto.*;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.ExplainResponse;
import ai.giskard.worker.ExplainTextResponse;
import ai.giskard.worker.RunModelForDataFrameResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.io.IOException;
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
    private final TransactionTemplate tt;


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
    public ExplainResponseDTO explain(@PathVariable @NotNull UUID modelId, @PathVariable @NotNull UUID datasetId, @RequestBody @NotNull PredictionInputDTO data) throws IOException {
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        ExplainResponse explanations = modelService.explain(model, dataset, data.getFeatures());
        ExplainResponseDTO result = new ExplainResponseDTO();
        explanations.getExplanationsMap().forEach((label, perFeatureExplanations) ->
            result.getExplanations().put(label, perFeatureExplanations.getPerFeatureMap()));
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
        ProjectModel model = giskardMapper.fromDTO(dto);
        model.setProject(project);
        modelRepository.save(model);
    }


    @PostMapping("models/explain-text/{featureName}")
    public ExplainTextResponseDTO explainText(@RequestParam @NotNull UUID modelId, @RequestParam @NotNull UUID datasetId, @PathVariable @NotNull String featureName, @RequestBody @NotNull PredictionInputDTO data) throws IOException {
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        long projectId = model.getProject().getId();
        InspectionSettings inspectionSettings = projectRepository.getMandatoryById(projectId).getInspectionSettings();
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        ExplainTextResponseDTO explanationRes = new ExplainTextResponseDTO();
        ExplainTextResponse textResponse = modelService.explainText(model, dataset, inspectionSettings, featureName, data.getFeatures());
        textResponse.getWeightsMap().forEach((label, weightPerFeature) ->
            explanationRes.getWeights().put(label, weightPerFeature.getWeightsList())
        );
        explanationRes.setWords(textResponse.getWordsList());
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
        RunModelForDataFrameResponse result = modelService.predict(model, dataset, data.getFeatures());
        Map<String, Float> allPredictions = new HashMap<>();
        if (model.getModelType() == ModelType.CLASSIFICATION) {
            result.getAllPredictions().getRows(0).getColumnsMap().forEach((label, proba) ->
                allPredictions.put(label, Float.parseFloat(proba))
            );
        }
        return new PredictionDTO(result.getPrediction(0), allPredictions);
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
