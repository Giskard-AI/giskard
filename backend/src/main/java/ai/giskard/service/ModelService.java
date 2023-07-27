package ai.giskard.service;

import ai.giskard.domain.ColumnType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.exception.MLWorkerIllegalReplyException;
import ai.giskard.exception.MLWorkerNotConnectedException;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.util.Strings;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
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
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;


    public MLWorkerWSRunModelForDataFrameDTO predict(ProjectModel model, Dataset dataset, Map<String, String> features) {
        MLWorkerID workerID = model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            return getRunModelForDataFrameResponse(model, dataset, features);
        }
        throw new MLWorkerNotConnectedException(workerID, log);
    }

    private MLWorkerWSRunModelForDataFrameDTO getRunModelForDataFrameResponse(ProjectModel model, Dataset dataset, Map<String, String> features) {
        // Initialize the parameters and build the Data Frame
        MLWorkerWSDataFrameDTO dataframe = MLWorkerWSDataFrameDTO.builder()
            .rows(
                List.of(
                    MLWorkerWSDataRowDTO.builder().columns(
                        features.entrySet().stream()
                            .filter(entry -> !shouldDrop(
                                dataset.getColumnDtypes().get(entry.getKey()),
                                entry.getValue()
                            )).collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue))
                    ).build()
                )
            ).build();

        MLWorkerWSRunModelForDataFrameParamDTO param = MLWorkerWSRunModelForDataFrameParamDTO.builder()
            .model(MLWorkerWSArtifactRefDTO.fromModel(model))
            .dataframe(dataframe)
            .build();

        if (dataset.getTarget() != null) {
            param.setTarget(dataset.getTarget());
        }
        if (dataset.getColumnTypes() != null) {
            param.setColumnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName));
        }
        if (dataset.getColumnDtypes() != null) {
            param.setColumnDtypes(dataset.getColumnDtypes());
        }

        // Perform the runModelForDataFrame action and parse the reply
        MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
            model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL,
            MLWorkerWSAction.runModelForDataFrame,
            param
        );
        if (result instanceof MLWorkerWSRunModelForDataFrameDTO response) {
            return response;
        } else if (result instanceof MLWorkerWSErrorDTO error) {
            throw new MLWorkerIllegalReplyException(error.getErrorType(), error.getErrorStr());
        }
        throw new MLWorkerIllegalReplyException("Invalid response", "Cannot get ML Worker RunModelForDataFrame reply");
    }

    public boolean shouldDrop(String columnDtype, String value) {
        return Objects.isNull(value) ||
            ((columnDtype.startsWith("int") || columnDtype.startsWith("float")) && Strings.isBlank(value));
    }

    public MLWorkerWSExplainDTO explain(ProjectModel model, Dataset dataset, Map<String, String> features) {
        MLWorkerID workerID = model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            MLWorkerWSExplainParamDTO param = MLWorkerWSExplainParamDTO.builder()
                .model(MLWorkerWSArtifactRefDTO.fromModel(model))
                .dataset(MLWorkerWSArtifactRefDTO.fromDataset(dataset))
                .columns(
                    features.entrySet().stream()
                        .filter(entry -> !shouldDrop(dataset.getColumnDtypes().get(entry.getKey()), entry.getValue()))
                        .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue))
                )
                .build();

            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(workerID, MLWorkerWSAction.explain, param);
            if (result instanceof MLWorkerWSExplainDTO response) {
                return response;
            } else if (result instanceof MLWorkerWSErrorDTO error) {
                throw new MLWorkerIllegalReplyException(error.getErrorType(), error.getErrorStr());
            }
            throw new MLWorkerIllegalReplyException("Invalid response", "Cannot get ML Worker Explain reply");
        }
        throw new MLWorkerNotConnectedException(workerID, log);
    }

    public MLWorkerWSExplainTextDTO explainText(ProjectModel model, Dataset dataset, String featureName, Map<String, String> features) {
        MLWorkerID workerID = model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            MLWorkerWSExplainTextParamDTO param = MLWorkerWSExplainTextParamDTO.builder()
                .model(MLWorkerWSArtifactRefDTO.fromModel(model))
                .featureName(featureName)
                .columns(features)
                .columnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName))
                .build();

            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                workerID,
                MLWorkerWSAction.explainText,
                param
            );
            if (result instanceof MLWorkerWSExplainTextDTO response) {
                return response;
            } else if (result instanceof MLWorkerWSErrorDTO error) {
                throw new MLWorkerIllegalReplyException(error.getErrorType(), error.getErrorStr());
            }
            throw new MLWorkerIllegalReplyException("Invalid response", "Cannot get ML Worker explainText reply");
        }
        throw new MLWorkerNotConnectedException(workerID, log);
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
        MLWorkerID workerID = model.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            // Initialize params
            MLWorkerWSRunModelParamDTO param = MLWorkerWSRunModelParamDTO.builder()
                .model(MLWorkerWSArtifactRefDTO.fromModel(model))
                .dataset(MLWorkerWSArtifactRefDTO.fromDataset(dataset, sample))
                .inspectionId(inspectionId)
                .projectKey(model.getProject().getKey())
                .build();

            // Execute runModel action
            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(workerID, MLWorkerWSAction.runModel, param);
            if (result instanceof MLWorkerWSEmptyDTO) {
                return;
            } else if (result instanceof MLWorkerWSErrorDTO error) {
                throw new MLWorkerIllegalReplyException(error.getErrorType(), error.getErrorStr());
            }
            throw new MLWorkerIllegalReplyException("Invalid response", "Cannot get ML Worker explainText reply");
        }
        throw new MLWorkerNotConnectedException(workerID, log);
    }
}
