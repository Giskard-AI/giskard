package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.PushDTO;
import ai.giskard.worker.SuggestFilterRequest;
import ai.giskard.worker.SuggestFilterResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
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
}
