package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.worker.MLWorkerGrpc;
import ai.giskard.worker.TestRegistryResponse;
import com.google.protobuf.Empty;
import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;

import static ai.giskard.utils.GRPCUtils.convertGRPCObject;

@Service
@RequiredArgsConstructor
public class MLWorkerCacheService {

    private final MLWorkerService mlWorkerService;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private List<TestFunctionDTO> testFunctions = Collections.emptyList();

    public List<TestFunctionDTO> findGiskardTest(boolean isInternal) {
        if (mlWorkerTunnelService.isClearCacheRequested()) {
            testFunctions = getTestFunctions(isInternal);
            mlWorkerTunnelService.setClearCacheRequested(false);
        }

        return testFunctions;
    }

    private List<TestFunctionDTO> getTestFunctions(boolean isInternal) {
        try (MLWorkerClient client = mlWorkerService.createClientNoError(isInternal)) {
            if (!isInternal && client == null) {
                // Fallback to internal ML worker to not display empty catalog
                return getTestFunctions(true).stream()
                    .map(dto -> dto.toBuilder().potentiallyUnavailable(true).build())
                    .toList();
            } else if (client == null) {
                return Collections.emptyList();
            }

            MLWorkerGrpc.MLWorkerBlockingStub blockingStub = client.getBlockingStub();
            TestRegistryResponse response = blockingStub.getTestRegistry(Empty.newBuilder().build());
            return response.getTestsMap().values().stream()
                .map(test -> convertGRPCObject(test, TestFunctionDTO.class))
                .toList();
        } catch (StatusRuntimeException e) {
            return Collections.emptyList();
        }
    }

}
