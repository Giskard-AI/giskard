package ai.giskard.service;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.TestCatalogDTO;
import ai.giskard.worker.TestRegistryResponse;
import com.google.protobuf.Empty;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import static ai.giskard.utils.GRPCUtils.convertGRPCObject;

@Service
@Transactional
@RequiredArgsConstructor
public class TestService {
    private final MLWorkerService mlWorkerService;
    private final ProjectRepository projectRepository;

    public TestCatalogDTO listTestsFromRegistry(Long projectId) {
        try (MLWorkerClient client = mlWorkerService.createClient(projectRepository.getById(projectId).isUsingInternalWorker())) {
            TestRegistryResponse response = client.getBlockingStub().getTestRegistry(Empty.newBuilder().build());
            return convertGRPCObject(response, TestCatalogDTO.class);
        }
    }
}
