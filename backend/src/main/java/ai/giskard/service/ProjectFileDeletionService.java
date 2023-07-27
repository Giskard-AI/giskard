package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.FileSystemUtils;

import java.io.IOException;
import java.nio.file.Path;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ProjectFileDeletionService {
    private final Logger log = LoggerFactory.getLogger(ProjectFileDeletionService.class);

    final FileLocationService locationService;
    final InspectionService inspectionService;
    final DatasetRepository datasetRepository;
    final ModelRepository modelRepository;
    final InspectionRepository inspectionRepository;
    final FeedbackRepository feedbackRepository;
    final PermissionEvaluator permissionEvaluator;

    public void deleteDataset(UUID datasetId) {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        permissionEvaluator.validateCanWriteProject(dataset.getProject().getId());

        log.info("Deleting inspections linked to dataset {}", datasetId);
        inspectionService.deleteInspections(inspectionRepository.findAllByDatasetId(datasetId));

        log.info("Deleting feedback linked to dataset {}", datasetId);
        feedbackRepository.deleteAll(feedbackRepository.findAllByDatasetId(datasetId));


        log.info("Deleting dataset from the database: {}", dataset.getId());
        datasetRepository.delete(dataset);

        Path datasetPath = locationService.resolvedDatasetPath(dataset);
        try {
            datasetRepository.flush();
            log.info("Removing dataset: {}", datasetPath);
            FileSystemUtils.deleteRecursively(datasetPath);
        } catch (Exception e) {
            throw new GiskardRuntimeException(String.format("Failed to remove dataset %s", datasetPath), e);
        }

    }

    public void deleteModel(UUID modelId) {
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        permissionEvaluator.validateCanWriteProject(model.getProject().getId());

        log.info("Deleting feedbacks for model: {}", model.getId());
        feedbackRepository.deleteAll(feedbackRepository.findAllByModelId(modelId));

        log.info("Deleting inspections for model: {}", model.getId());
        inspectionService.deleteInspections(inspectionRepository.findAllByModelId(modelId));

        log.info("Deleting model from the database: {}", model.getId());
        modelRepository.delete(model);

        Path modelPath = locationService.resolvedModelPath(model);
        try {
            modelRepository.flush();
            Path modelsDirectory = locationService.modelsDirectory();
            log.info("Removing model: {}", modelPath);
            FileSystemUtils.deleteRecursively(modelsDirectory.resolve(modelPath));
        } catch (IOException e) {
            throw new GiskardRuntimeException(String.format("Failed to remove model files %s", modelPath), e);
        }

    }


}
