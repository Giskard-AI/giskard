package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ColumnType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.exception.MLWorkerIllegalReplyException;
import ai.giskard.exception.MLWorkerNotConnectedException;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.web.dto.ApplyPushDTO;
import ai.giskard.web.dto.PredictionInputDTO;
import com.google.common.collect.Maps;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.util.Strings;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class PushController {
    private final ModelRepository modelRepository;
    private final PermissionEvaluator permissionEvaluator;
    private final DatasetRepository datasetRepository;

    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final MLWorkerWSService mlWorkerWSService;


    @PostMapping("/pushes/{modelId}/{datasetId}/{idx}")
    public MLWorkerWSGetPushResultDTO getPushes(@PathVariable @NotNull UUID modelId,
                                                @PathVariable @NotNull UUID datasetId,
                                                @PathVariable @NotNull int idx,
                                                @RequestBody @NotNull PredictionInputDTO data) {
        ProjectModel model = modelRepository.getMandatoryById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        Map<String, String> features = data.getFeatures();

        MLWorkerWSArtifactRefDTO datasetRef = MLWorkerWSArtifactRefDTO.fromDataset(dataset);
        MLWorkerWSArtifactRefDTO modelRef = MLWorkerWSArtifactRefDTO.fromModel(model);

        MLWorkerWSGetPushDTO.MLWorkerWSGetPushDTOBuilder paramBuilder = MLWorkerWSGetPushDTO.builder()
            .dataset(datasetRef)
            .model(modelRef)
            .rowIdx(idx);

        if (features != null) {
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

            paramBuilder.dataframe(dataframe);
        }

        if (dataset.getTarget() != null) {
            paramBuilder.target(dataset.getTarget());
        }
        if (dataset.getColumnTypes() != null) {
            paramBuilder.columnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName));
        }
        if (dataset.getColumnDtypes() != null) {
            paramBuilder.columnDtypes(dataset.getColumnDtypes());
        }

        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.EXTERNAL)) {
            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                MLWorkerID.EXTERNAL,
                MLWorkerWSAction.GET_PUSH,
                paramBuilder.build()
            );

            if (result instanceof MLWorkerWSGetPushResultDTO response) {
                return response;
            } else if (result instanceof MLWorkerWSErrorDTO error) {
                throw new MLWorkerIllegalReplyException(error);
            }
            throw new MLWorkerIllegalReplyException("Cannot get ML Worker GetPushResult reply");
        }

        throw new MLWorkerNotConnectedException(MLWorkerID.EXTERNAL);
    }

    @PostMapping("/push/apply")
    public MLWorkerWSGetPushResultDTO applyPushSuggestion(@RequestBody ApplyPushDTO applyPushDTO) {
        ProjectModel model = modelRepository.getMandatoryById(applyPushDTO.getModelId());
        Dataset dataset = datasetRepository.getMandatoryById(applyPushDTO.getDatasetId());
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        Map<String, String> features = applyPushDTO.getFeatures();

        MLWorkerWSArtifactRefDTO datasetRef = MLWorkerWSArtifactRefDTO.fromDataset(dataset);
        MLWorkerWSArtifactRefDTO modelRef = MLWorkerWSArtifactRefDTO.fromModel(model);

        MLWorkerWSGetPushDTO.MLWorkerWSGetPushDTOBuilder paramBuilder = MLWorkerWSGetPushDTO.builder()
            .dataset(datasetRef)
            .model(modelRef)
            .rowIdx(applyPushDTO.getRowIdx())
            .pushKind(applyPushDTO.getPushKind())
            .ctaKind(applyPushDTO.getCtaKind());

        if (features != null) {
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

            paramBuilder.dataframe(dataframe);
        }

        if (dataset.getTarget() != null) {
            paramBuilder.target(dataset.getTarget());
        }
        if (dataset.getColumnTypes() != null) {
            paramBuilder.columnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName));
        }
        if (dataset.getColumnDtypes() != null) {
            paramBuilder.columnDtypes(dataset.getColumnDtypes());
        }

        paramBuilder.pushKind(applyPushDTO.getPushKind());
        paramBuilder.ctaKind(applyPushDTO.getCtaKind());

        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.EXTERNAL)) {
            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                MLWorkerID.EXTERNAL,
                MLWorkerWSAction.GET_PUSH,
                paramBuilder.build()
            );

            if (result instanceof MLWorkerWSGetPushResultDTO response) {
                return response;
            } else if (result instanceof MLWorkerWSErrorDTO error) {
                throw new MLWorkerIllegalReplyException(error);
            }
            throw new MLWorkerIllegalReplyException("Cannot get ML Worker GetPushResult reply");
        }

        throw new MLWorkerNotConnectedException(MLWorkerID.EXTERNAL);
    }

    // Probably move this to a util class.
    public boolean shouldDrop(String columnDtype, String value) {
        return Objects.isNull(columnDtype) || Objects.isNull(value) ||
            ((columnDtype.startsWith("int") || columnDtype.startsWith("float")) && Strings.isBlank(value));
    }
}
