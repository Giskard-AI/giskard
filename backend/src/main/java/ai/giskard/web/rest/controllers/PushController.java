package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ColumnType;
import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.GRPCMapper;
import ai.giskard.service.PushService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.ApplyPushDTO;
import ai.giskard.web.dto.PredictionInputDTO;
import ai.giskard.web.dto.PushDTO;
import ai.giskard.worker.*;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.util.Strings;
import org.springframework.web.bind.annotation.*;

import javax.validation.constraints.NotNull;
import java.util.HashMap;
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
    private final PushService pushService;

    private final MLWorkerService mlWorkerService;
    private final GRPCMapper grpcMapper;


    @PostMapping("/pushes/{modelId}/{datasetId}/{idx}")
    public Map<String, PushDTO> getPushes(@PathVariable @NotNull UUID modelId,
                                          @PathVariable @NotNull UUID datasetId,
                                          @PathVariable @NotNull int idx,
                                          @RequestBody @NotNull PredictionInputDTO data) {
        ProjectModel model = modelRepository.getById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        Project project = dataset.getProject();
        Map<String, String> features = data.getFeatures();

        ArtifactRef datasetRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(dataset.getId().toString()).build();
        ArtifactRef modelRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(model.getId().toString()).build();

        try (MLWorkerClient client = mlWorkerService.createClient(project.isUsingInternalWorker())) {
            SuggestFilterRequest.Builder requestBuilder = SuggestFilterRequest.newBuilder()
                .setDataset(datasetRef)
                .setModel(modelRef)
                .setRowidx(idx);

            if (features != null) {
                requestBuilder.setDataframe(
                    DataFrame.newBuilder()
                        .addRows(DataRow.newBuilder().putAllColumns(
                            features.entrySet().stream()
                                .filter(entry -> !shouldDrop(dataset.getColumnDtypes().get(entry.getKey()), entry.getValue()))
                                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue))
                        ))
                        .build()
                );
            }

            if (dataset.getTarget() != null) {
                requestBuilder.setTarget(dataset.getTarget());
            }
            if (dataset.getColumnTypes() != null) {
                requestBuilder.putAllColumnTypes(Maps.transformValues(dataset.getColumnTypes(), ColumnType::getName));
            }
            if (dataset.getColumnDtypes() != null) {
                requestBuilder.putAllColumnDtypes(dataset.getColumnDtypes());
            }

            SuggestFilterResponse resp = client.getBlockingStub().suggestFilter(requestBuilder.build());

            Map<String, PushDTO> dtos = new HashMap<>();

            dtos.put("perturbation", PushDTO.fromGrpc(resp.getPerturbation()));
            dtos.put("contribution", PushDTO.fromGrpc(resp.getContribution()));
            dtos.put("borderline", PushDTO.fromGrpc(resp.getBorderline()));
            dtos.put("overconfidence", PushDTO.fromGrpc(resp.getOverconfidence()));

            return dtos;
        }
    }

    @PostMapping("/push/apply")
    public String applyPushSuggestion(@RequestBody ApplyPushDTO applyPushDTO) {
        ProjectModel model = modelRepository.getById(applyPushDTO.getModelId());
        Dataset dataset = datasetRepository.getMandatoryById(applyPushDTO.getDatasetId());
        Project project = dataset.getProject();

        ArtifactRef datasetRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(dataset.getId().toString()).build();
        ArtifactRef modelRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(model.getId().toString()).build();

        try (MLWorkerClient client = mlWorkerService.createClient(project.isUsingInternalWorker())) {
            SuggestFilterRequest.Builder requestBuilder = SuggestFilterRequest.newBuilder()
                .setDataset(datasetRef)
                .setModel(modelRef)
                .setRowidx(applyPushDTO.getRowIdx())
                .setCtaKind(applyPushDTO.getCtaKind())
                .setPushKind(applyPushDTO.getPushKind())
                .setProjectKey(project.getKey())
                .setDataframe(
                    DataFrame.newBuilder()
                        .addRows(DataRow.newBuilder().putAllColumns(
                            applyPushDTO.getFeatures().entrySet().stream()
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

            SuggestFilterResponse resp = client.getBlockingStub().suggestFilter(requestBuilder.build());
            return resp.getObjectUuid();
        }
    }

    // Probably move this to a util class.
    public boolean shouldDrop(String columnDtype, String value) {
        return Objects.isNull(columnDtype) || Objects.isNull(value) ||
            ((columnDtype.startsWith("int") || columnDtype.startsWith("float")) && Strings.isBlank(value));
    }
}
