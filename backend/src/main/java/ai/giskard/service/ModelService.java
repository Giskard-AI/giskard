package ai.giskard.service;

import ai.giskard.domain.ColumnMeaning;
import ai.giskard.domain.InspectionSettings;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.FeedbackRepository;
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
import java.util.Objects;
import java.util.UUID;

@Service
@Transactional
@RequiredArgsConstructor
public class ModelService {
    private final DatasetRepository datasetRepository;
    final FeedbackRepository feedbackRepository;
    final ModelRepository modelRepository;
    private final PermissionEvaluator permissionEvaluator;
    private final InspectionRepository inspectionRepository;
    private final Logger log = LoggerFactory.getLogger(ModelService.class);
    private final MLWorkerService mlWorkerService;
    private final FileLocationService fileLocationService;
    private final GRPCMapper grpcMapper;


    public RunModelForDataFrameResponse predict(ProjectModel model, Dataset dataset, Map<String, String> features) {
        RunModelForDataFrameResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            response = getRunModelForDataFrameResponse(model, dataset, features, client);
        }
        return response;
    }

    private RunModelForDataFrameResponse getRunModelForDataFrameResponse(ProjectModel model, Dataset dataset, Map<String, String> features, MLWorkerClient client) {
        RunModelForDataFrameResponse response;
        RunModelForDataFrameRequest.Builder requestBuilder = RunModelForDataFrameRequest.newBuilder()
            .setModel(grpcMapper.createRef(model))
            .setDataframe(
                DataFrame.newBuilder()
                    .addRows(DataRow.newBuilder().putAllColumns(Maps.filterValues(features, Objects::nonNull)))
                    .build()
            );
        if (dataset.getTarget() != null) {
            requestBuilder.setTarget(dataset.getTarget());
        }
        if (dataset.getColumnMeanings() != null) {
            requestBuilder.putAllColumnMeanings(Maps.transformValues(dataset.getColumnMeanings(), ColumnMeaning::getName));
        }
        if (dataset.getColumnTypes() != null) {
            requestBuilder.putAllColumnTypes(dataset.getColumnTypes());
        }
        response = client.getBlockingStub().runModelForDataFrame(requestBuilder.build());
        return response;
    }

    public ExplainResponse explain(ProjectModel model, Dataset dataset, Map<String, String> features) {
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            ExplainRequest request = ExplainRequest.newBuilder()
                .setModel(grpcMapper.createRef(model))
                .setDataset(grpcMapper.createRef(dataset))
                .putAllColumns(Maps.filterValues(features, Objects::nonNull))
                .build();

            return client.getBlockingStub().explain(request);
        }
    }

    public ExplainTextResponse explainText(ProjectModel model, Dataset dataset, InspectionSettings inspectionSettings, String featureName, Map<String, String> features) throws IOException {
        ExplainTextResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            response = client.getBlockingStub().explainText(
                ExplainTextRequest.newBuilder()
                    .setModel(grpcMapper.createRef(model))
                    .setFeatureName(featureName)
                    .putAllColumns(features)
                    .putAllColumnMeanings(Maps.transformValues(dataset.getColumnMeanings(), ColumnMeaning::getName))
                    .setNSamples(inspectionSettings.getLimeNumberSamples())
                    .build()
            );
        }
        return response;
    }

    public Inspection createInspection(UUID modelId, UUID datasetId) throws IOException {
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

    private RunModelResponse predictSerializedDataset(ProjectModel model, Dataset dataset) {
        RunModelResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            RunModelRequest request = RunModelRequest.newBuilder()
                .setModel(grpcMapper.createRef(model))
                .setDataset(grpcMapper.createRef(dataset))
                .build();

            response = client.getBlockingStub().runModel(request);
        }

        return response;
    }
}
