package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.PushDTO;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.SuggestFilterRequest;
import ai.giskard.worker.SuggestFilterResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
//@Transactional
@RequiredArgsConstructor
public class PushService {


    private final MLWorkerService mlWorkerService;
    private final GRPCMapper grpcMapper;

    public List<PushDTO> getPushes(ProjectModel model, Dataset dataset, int idx) {
        try (MLWorkerClient client = mlWorkerService.createClient(true)) {
            SuggestFilterResponse resp = client.getBlockingStub().suggestFilter(SuggestFilterRequest.newBuilder()
                .setDataset(grpcMapper.createRef(dataset))
                .setModel(grpcMapper.createRef(model))
                .setRowidx(idx)
                .build());

            return resp.getPushesList().stream()
                .map(PushDTO::fromGrpc)
                .collect(Collectors.toList());
        }
    }

    // Applying a push suggestion should always return the ID of the created object :)
    public String applyPushSuggestion(String projectKey, ArtifactRef model, ArtifactRef dataset, int idx, int pushIdx, int uploadKind) {
        try (MLWorkerClient client = mlWorkerService.createClient(true)) {
            SuggestFilterResponse resp = client.getBlockingStub().suggestFilter(SuggestFilterRequest.newBuilder()
                .setDataset(dataset)
                .setModel(model)
                .setRowidx(idx)
                .setUploadKindValue(uploadKind)
                .setUploadIndex(pushIdx)
                .setProjectKey(projectKey)
                .build());

            return "";
        }
    }
}
