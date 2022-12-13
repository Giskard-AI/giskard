package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.security.PermissionEvaluator;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
@RequiredArgsConstructor
public class ProjectFileDeletionService {
    private final Logger log = LoggerFactory.getLogger(ProjectFileDeletionService.class);

    final FileLocationService locationService;
    final InspectionService inspectionService;
    final DatasetRepository datasetRepository;
    final ModelRepository modelRepository;
    final TestSuiteRepository testSuiteRepository;
    final InspectionRepository inspectionRepository;
    final FeedbackRepository feedbackRepository;
    final PermissionEvaluator permissionEvaluator;

    @Transactional
    public void deleteDataset(Long datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        permissionEvaluator.validateCanWriteProject(dataset.getProject().getId());

        log.info("Deleting test suites linked to dataset {}", datasetId);
        testSuiteRepository.deleteAll(testSuiteRepository.findByDatasetId(datasetId));

        log.info("Deleting inspections linked to dataset {}", datasetId);
        inspectionService.deleteInspections(inspectionRepository.findAllByDatasetId(datasetId));

        log.info("Deleting feedback linked to dataset {}", datasetId);
        feedbackRepository.deleteAll(feedbackRepository.findAllByDatasetId(datasetId));


        log.info("Deleting dataset from the database: {}", dataset.getId());
        datasetRepository.delete(dataset);

        try {
            datasetRepository.flush();
            Path datasetPath = locationService.datasetsDirectory(dataset.getProject().getKey()).resolve(dataset.getFileName());
            log.info("Removing dataset file: {}", datasetPath.getFileName());
            Files.deleteIfExists(datasetPath);
        } catch (Exception e) {
            throw new GiskardRuntimeException(String.format("Failed to remove dataset %s", dataset.getFileName()), e);
        }

    }

    @Transactional
    public void deleteModel(Long modelId) {
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanWriteProject(model.getProject().getId());

        log.info("Deleting test suites for model: {}", model.getId());
        testSuiteRepository.deleteAll(testSuiteRepository.findAllByModelId(modelId));

        log.info("Deleting feedbacks for model: {}", model.getId());
        feedbackRepository.deleteAll(feedbackRepository.findAllByModelId(modelId));

        log.info("Deleting inspections for model: {}", model.getId());
        inspectionService.deleteInspections(inspectionRepository.findAllByModelId(modelId));

        log.info("Deleting model from the database: {}", model.getId());
        modelRepository.delete(model);


        try {
            modelRepository.flush();
            Path modelsDirectory = locationService.modelsDirectory(model.getProject().getKey());
            log.info("Removing model file: {}", model.getFileName());
            Files.deleteIfExists(modelsDirectory.resolve(model.getFileName()));
            log.info("Removing model requirements file: {}", modelsDirectory.getFileName());
            Files.deleteIfExists(modelsDirectory.resolve(model.getRequirementsFileName()));
        } catch (IOException e) {
            throw new GiskardRuntimeException(String.format("Failed to remove model files %s", model.getFileName()), e);
        }

    }


}
