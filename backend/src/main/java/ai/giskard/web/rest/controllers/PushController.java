package ai.giskard.web.rest.controllers;

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
import ai.giskard.web.dto.PushDTO;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.SuggestFilterRequest;
import ai.giskard.worker.SuggestFilterResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import javax.validation.constraints.NotNull;
import java.util.List;
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


    @GetMapping("/pushes/{modelId}/{datasetId}/{idx}")
    public List<PushDTO> getPushes(@PathVariable @NotNull UUID modelId, @PathVariable @NotNull UUID datasetId, @PathVariable @NotNull int idx) {
        ProjectModel model = modelRepository.getById(modelId);
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        Project project = dataset.getProject();

        ArtifactRef datasetRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(dataset.getId().toString()).build();
        ArtifactRef modelRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(model.getId().toString()).build();

        try (MLWorkerClient client = mlWorkerService.createClient(true)) {
            SuggestFilterResponse resp = client.getBlockingStub().suggestFilter(SuggestFilterRequest.newBuilder()
                .setDataset(datasetRef)
                .setModel(modelRef)
                .setRowidx(idx)
                .build());

            return resp.getPushesList().stream()
                .map(PushDTO::fromGrpc)
                .collect(Collectors.toList());
        }
    }

    @PostMapping("/push/apply")
    public String applyPushSuggestion(@RequestBody ApplyPushDTO applyPushDTO) {
        ProjectModel model = modelRepository.getById(applyPushDTO.getModelId());
        Dataset dataset = datasetRepository.getMandatoryById(applyPushDTO.getDatasetId());
        Project project = dataset.getProject();

        ArtifactRef datasetRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(dataset.getId().toString()).build();
        ArtifactRef modelRef = ArtifactRef.newBuilder().setProjectKey(project.getKey()).setId(model.getId().toString()).build();

        return pushService.applyPushSuggestion(
            project.getKey(),
            modelRef,
            datasetRef,
            applyPushDTO.getRowIdx(),
            applyPushDTO.getPushIdx(),
            applyPushDTO.getKind()
        );
    }
}
