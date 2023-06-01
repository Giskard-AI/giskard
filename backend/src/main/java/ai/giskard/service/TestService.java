package ai.giskard.service;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestExecutionRepository;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.TestCatalogDTO;
import ai.giskard.worker.TestRegistryResponse;
import com.google.protobuf.Empty;
import ai.giskard.web.dto.ml.TestDTO;
import ai.giskard.web.dto.ml.TestExecutionResultDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.RunTestRequest;
import ai.giskard.worker.TestResultMessage;
import com.google.common.collect.Lists;
import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

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
