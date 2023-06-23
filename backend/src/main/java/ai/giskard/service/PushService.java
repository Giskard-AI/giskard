package ai.giskard.service;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.SuggestFilterRequest;
import ai.giskard.worker.SuggestFilterResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
//@Transactional
@RequiredArgsConstructor
public class PushService {


    private final MLWorkerService mlWorkerService;
    private final GRPCMapper grpcMapper;

    // Applying a push suggestion should always return the ID of the created object :)
    public String applyPushSuggestion(String projectKey, ArtifactRef model, ArtifactRef dataset, int idx, int pushIdx, int uploadKind) {
        try (MLWorkerClient client = mlWorkerService.createClient(false)) {
            SuggestFilterResponse resp = client.getBlockingStub().suggestFilter(SuggestFilterRequest.newBuilder()
                .setDataset(dataset)
                .setModel(model)
                .setRowidx(idx)
                .setCtaKindValue(uploadKind)
                .setProjectKey(projectKey)
                .build());

            return "";
        }
    }
}
