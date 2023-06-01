package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.TestFunctionService;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.worker.CatalogResponse;
import ai.giskard.worker.MLWorkerGrpc;
import com.google.protobuf.Empty;
import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;
import java.util.stream.Stream;

import static ai.giskard.utils.GRPCUtils.convertGRPCObject;

@Service
@RequiredArgsConstructor
public class MLWorkerCacheService {

    private final MLWorkerService mlWorkerService;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private final TestFunctionService testFunctionService;
    private final TestFunctionRepository testFunctionRepository;
    private final ProjectRepository projectRepository;
    private final GiskardMapper giskardMapper;
    private List<TestFunctionDTO> testFunctions = Collections.emptyList();

    @Transactional
    public List<TestFunctionDTO> getCatalog(long projectId) {
        return Stream.concat(testFunctionRepository.findAll().stream()
                    .filter(t -> t.getTags().contains("pickle"))
                    .map(giskardMapper::toDTO),
                findGiskardTest(projectRepository.getById(projectId).isUsingInternalWorker()).stream())
            .toList();
    }

    public List<TestFunctionDTO> findGiskardTest(boolean isInternal) {
        if (isInternal) {
            // Only cache external ML worker
            return getTestFunctions(true);
        }

        if (mlWorkerTunnelService.isClearCacheRequested()) {
            testFunctions = getTestFunctions(false);
            testFunctionService.saveAll(testFunctions);
            mlWorkerTunnelService.setClearCacheRequested(false);
        }

        return testFunctions;
    }

    private List<TestFunctionDTO> getTestFunctions(boolean isInternal) {
        try (MLWorkerClient client = mlWorkerService.createClientNoError(isInternal)) {
            if (!isInternal && client == null) {
                // Fallback to internal ML worker to not display empty catalog
                return getTestFunctions(true).stream()
                    .peek(dto -> dto.setPotentiallyUnavailable(true))
                    .toList();
            } else if (client == null) {
                return Collections.emptyList();
            }

            MLWorkerGrpc.MLWorkerBlockingStub blockingStub = client.getBlockingStub();
            CatalogResponse response = blockingStub.getCatalog(Empty.newBuilder().build());
            return response.getTestsMap().values().stream()
                .map(test -> convertGRPCObject(test, TestFunctionDTO.class))
                .toList();
        } catch (StatusRuntimeException e) {
            return Collections.emptyList();
        }
    }

}
