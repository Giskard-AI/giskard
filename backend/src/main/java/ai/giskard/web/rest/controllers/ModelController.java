package ai.giskard.web.rest.controllers;

import ai.giskard.domain.InspectionSettings;
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
import ai.giskard.worker.ExplainResponse;
import ai.giskard.worker.RunModelForDataFrameResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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

    @GetMapping("models/{modelId}/metadata")
    @Transactional
    public ModelMetadataDTO getModelMetadata(@PathVariable @NotNull Long modelId) {
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        return giskardMapper.modelToModelMetadataDTO(model);
    }

    @PostMapping("models/{modelId}/explain/{datasetId}")
    @Transactional
    public ExplainResponseDTO explain(@PathVariable @NotNull Long modelId, @PathVariable @NotNull Long datasetId, @RequestBody @NotNull PredictionInputDTO data) throws IOException {
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        Dataset dataset = datasetRepository.getById(datasetId);
        ExplainResponse explanations = modelService.explain(model, dataset, data.getFeatures());
        ExplainResponseDTO result = new ExplainResponseDTO();
        explanations.getExplanationsMap().forEach((label, perFeatureExplanations) ->
            result.getExplanations().put(label, perFeatureExplanations.getPerFeatureMap()));
        return result;
    }

    @PostMapping("models/explain-text/{featureName}")
    @Transactional
    public ExplainTextResponseDTO explainText(@RequestParam @NotNull Long modelId, @RequestParam @NotNull Long datasetId, @PathVariable @NotNull String featureName, @RequestBody @NotNull PredictionInputDTO data) throws IOException {
        ProjectModel model = modelRepository.getById(modelId);
        Dataset dataset = datasetRepository.getById(datasetId);
        long projectId = model.getProject().getId();
        InspectionSettings inspectionSettings = projectRepository.getById(projectId).getInspectionSettings();
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        ExplainTextResponseDTO explanationRes = new ExplainTextResponseDTO();
        modelService.explainText(model, dataset, inspectionSettings, featureName, data.getFeatures()).getExplanationTextMap().forEach((label, perFeatureExplanation) ->
            explanationRes.getExplanations().put(label, perFeatureExplanation.getExplanationsList().stream().map((x) -> x.getExplanationMap()).collect(Collectors.toList()))
        );
        return explanationRes;
    }

    @DeleteMapping("models/{modelId}")
    public MessageDTO deleteModel(@PathVariable @NotNull Long modelId) {
        deletionService.deleteModel(modelId);
        return new MessageDTO("Model {} has been deleted", modelId);
    }

    @PostMapping("models/{modelId}/predict")
    @Transactional
    public PredictionDTO predict(@PathVariable @NotNull Long modelId, @RequestBody @NotNull PredictionInputDTO data) throws IOException {
        ProjectModel model = modelRepository.getById(modelId);
        Dataset dataset = datasetRepository.getById(data.getDatasetId());
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        RunModelForDataFrameResponse result = modelService.predict(model, dataset, data.getFeatures());
        Map<String, Float> allPredictions = new HashMap<>();
        if (ModelType.isClassification(model.getModelType())) {
            result.getAllPredictions().getRows(0).getColumnsMap().forEach((label, proba) ->
                allPredictions.put(label, Float.parseFloat(proba))
            );
        }
        return new PredictionDTO(result.getPrediction(0), allPredictions);
    }

    @GetMapping("models/prepare-delete/{modelId}")
    public PrepareDeleteDTO prepareModelDelete(@PathVariable @NotNull Long modelId) {
        return usageService.prepareDeleteModel(modelId);
    }
}
