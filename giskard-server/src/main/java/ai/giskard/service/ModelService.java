package ai.giskard.service;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.InspectionSettings;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.worker.*;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

@Service
@Transactional
@RequiredArgsConstructor
public class ModelService {
    private final Logger log = LoggerFactory.getLogger(ModelService.class);

    final DatasetRepository datasetRepository;
    final ModelRepository modelRepository;
    final PermissionEvaluator permissionEvaluator;
    final InspectionRepository inspectionRepository;
    private final MLWorkerService mlWorkerService;
    private final FileLocationService locationService;
    private final FileLocationService fileLocationService;
    private final GRPCMapper grpcMapper;

    public RunModelForDataFrameResponse predict(ProjectModel model, Dataset dataset, Map<String, String> features) throws IOException {
        RunModelForDataFrameResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.runModelForDataframe(model, dataset, features);
        }
        return response;
    }

    public ExplainResponse explain(ProjectModel model, Dataset dataset, Map<String, String> features) throws IOException {

        ExplainResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.explain(
                model,
                dataset,
                features);
        }
        return response;
    }


    public ExplainTextResponse explainText(ProjectModel model, Dataset dataset, InspectionSettings inspectionSettings, String featureName, Map<String, String> features) throws IOException {
        ExplainTextResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.getBlockingStub().explainText(
                ExplainTextRequest.newBuilder()
                    .setModel(grpcMapper.serialize(model))
                    .setFeatureName(featureName)
                    .putAllColumns(features)
                    .putAllFeatureTypes(Maps.transformValues(dataset.getFeatureTypes(), FeatureType::getName))
                    .setNSamples(inspectionSettings.getLimeNumberSamples())
                    .build()
            );
        }
        return response;
    }


    public Inspection createInspection(Long modelId, Long datasetId) throws IOException {
        log.info("Creating inspection for model {} and dataset {}", modelId, datasetId);
        ProjectModel model = modelRepository.getById(modelId);
        Dataset dataset = datasetRepository.getById(datasetId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());

        Inspection inspection = new Inspection();
        inspection.setDataset(dataset);
        inspection.setModel(model);
        inspection = inspectionRepository.save(inspection);

        RunModelResponse predictions = predictSerializedDataset(model, dataset);
        if (predictions == null) {
            return inspection;
        }
        Path inspectionPath = fileLocationService.resolvedInspectionPath(model.getProject().getKey(), inspection.getId());
        Files.createDirectories(inspectionPath);
        Files.write(inspectionPath.resolve("predictions.csv"), predictions.getResultsCsvBytes().toByteArray());
        Files.write(inspectionPath.resolve("calculated.csv"), predictions.getCalculatedCsvBytes().toByteArray());
        return inspection;
    }

    private RunModelResponse predictSerializedDataset(ProjectModel model, Dataset dataset) throws IOException {
        RunModelResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.runModelForDataStream(model, dataset);
        }

        return response;
    }

    public void deleteModel(Long modelId) {
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanWriteProject(model.getProject().getId());

        log.info("Deleting model from the database: {}", model.getId());
        modelRepository.delete(model);

        Path modelsDirectory = locationService.modelsDirectory(model.getProject().getKey());

        try {
            log.info("Removing model file: {}", model.getFileName());
            Files.deleteIfExists(modelsDirectory.resolve(model.getFileName()));
            log.info("Removing model requirements file: {}", modelsDirectory.getFileName());
            Files.deleteIfExists(modelsDirectory.resolve(model.getRequirementsFileName()));
        } catch (IOException e) {
            throw new GiskardRuntimeException(String.format("Failed to remove model files %s", model.getFileName()), e);
        }

    }
}
