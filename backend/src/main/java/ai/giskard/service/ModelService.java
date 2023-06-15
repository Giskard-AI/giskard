package ai.giskard.service;

import ai.giskard.domain.ColumnType;
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
import org.apache.logging.log4j.util.Strings;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
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
                    .addRows(DataRow.newBuilder().putAllColumns(
                        features.entrySet().stream()
                            .filter(entry -> !shouldDrop(dataset.getColumnDtypes().get(entry.getKey()), entry.getValue()))
                            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue))
                    ))
                    .build()
            );
        if (dataset.getTarget() != null) {
            requestBuilder.setTarget(dataset.getTarget());
        }
        if (dataset.getColumnTypes() != null) {
            requestBuilder.putAllColumnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName));
        }
        if (dataset.getColumnDtypes() != null) {
            requestBuilder.putAllColumnDtypes(dataset.getColumnDtypes());
        }
        response = client.getBlockingStub().runModelForDataFrame(requestBuilder.build());
        return response;
    }

    public boolean shouldDrop(String columnDtype, String value) {
        return Objects.isNull(value) ||
            ((columnDtype.startsWith("int") || columnDtype.startsWith("float")) && Strings.isBlank(value));
    }

    public ExplainResponse explain(ProjectModel model, Dataset dataset, Map<String, String> features) {
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            ExplainRequest request = ExplainRequest.newBuilder()
                .setModel(grpcMapper.createRef(model))
                .setDataset(grpcMapper.createRef(dataset, false))
                .putAllColumns(features.entrySet().stream()
                    .filter(entry -> !shouldDrop(dataset.getColumnDtypes().get(entry.getKey()), entry.getValue()))
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)))
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
                    .putAllColumnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName))
                    .setNSamples(inspectionSettings.getLimeNumberSamples())
                    .build()
            );
        }
        return response;
    }

    public Inspection createInspection(String name, UUID modelId, UUID datasetId, boolean sample) {
        log.info("Creating inspection for model {} and dataset {}", modelId, datasetId);
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());

        Inspection inspection = new Inspection();

        if (name == null || name.isEmpty())
            inspection.setName("Unnamed session");
        else
            inspection.setName(name);

        inspection.setDataset(dataset);
        inspection.setModel(model);
        inspection.setSample(sample);

        inspection = inspectionRepository.save(inspection);

        predictSerializedDataset(model, dataset, inspection.getId(), sample);
        return inspection;
    }

    protected void predictSerializedDataset(ProjectModel model, Dataset dataset, Long inspectionId, boolean sample) {
        try (MLWorkerClient client = mlWorkerService.createClient(model.getProject().isUsingInternalWorker())) {
            RunModelRequest request = RunModelRequest.newBuilder()
                .setModel(grpcMapper.createRef(model))
                .setDataset(grpcMapper.createRef(dataset, sample))
                .setInspectionId(inspectionId)
                .setProjectKey(model.getProject().getKey())
                .build();
            client.getBlockingStub().runModel(request);
        }
    }
}
