package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.SliceFunctionRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.SliceFunctionService;
import ai.giskard.service.TestFunctionService;
import ai.giskard.web.dto.CatalogDTO;
import ai.giskard.web.dto.SliceFunctionDTO;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.worker.CatalogResponse;
import ai.giskard.worker.MLWorkerGrpc;
import com.google.protobuf.Empty;
import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.stream.Stream;

import static ai.giskard.utils.GRPCUtils.convertGRPCObject;

@Service
@RequiredArgsConstructor
public class MLWorkerCacheService {

    private final MLWorkerService mlWorkerService;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private final TestFunctionService testFunctionService;
    private final TestFunctionRepository testFunctionRepository;
    private final SliceFunctionService sliceFunctionService;
    private final SliceFunctionRepository sliceFunctionRepository;
    private final ProjectRepository projectRepository;
    private final GiskardMapper giskardMapper;
    private CatalogDTO catalogWithoutPickles = new CatalogDTO();

    @Transactional
    public CatalogDTO getCatalog(long projectId) {
        CatalogDTO catalog = findGiskardTest(projectRepository.getById(projectId).isUsingInternalWorker());

        return CatalogDTO.builder()
            .tests(Stream.concat(
                    testFunctionRepository.findAllPickles().stream().map(giskardMapper::toDTO),
                    catalog.getTests().stream()
                )
                .toList())
            .slices(Stream.concat(
                    sliceFunctionRepository.findAllPickles().stream().map(giskardMapper::toDTO),
                    catalog.getSlices().stream()
                )
                .toList())
            .build();
    }

    public CatalogDTO findGiskardTest(boolean isInternal) {
        if (isInternal) {
            // Only cache external ML worker
            return getTestFunctions(true);
        }

        if (mlWorkerTunnelService.isClearCacheRequested()) {
            catalogWithoutPickles = getTestFunctions(false);
            testFunctionService.saveAll(catalogWithoutPickles.getTests());
            sliceFunctionService.saveAll(catalogWithoutPickles.getSlices());
            mlWorkerTunnelService.setClearCacheRequested(false);
        }

        return catalogWithoutPickles;
    }

    private CatalogDTO getTestFunctions(boolean isInternal) {
        try (MLWorkerClient client = mlWorkerService.createClientNoError(isInternal)) {
            if (!isInternal && client == null) {
                // Fallback to internal ML worker to not display empty catalog
                CatalogDTO catalog = getTestFunctions(true);
                catalog.getTests().forEach(fn -> fn.setPotentiallyUnavailable(true));
                catalog.getSlices().forEach(fn -> fn.setPotentiallyUnavailable(true));
                return catalog;
            } else if (client == null) {
                return new CatalogDTO();
            }

            MLWorkerGrpc.MLWorkerBlockingStub blockingStub = client.getBlockingStub();
            CatalogResponse response = blockingStub.getCatalog(Empty.newBuilder().build());
            return CatalogDTO.builder()
                .tests(response.getTestsMap().values().stream()
                    .map(test -> convertGRPCObject(test, TestFunctionDTO.class))
                    .toList())
                .slices(response.getSlicesMap().values().stream()
                    .map(test -> convertGRPCObject(test, SliceFunctionDTO.class))
                    .toList())
                .build();
        } catch (StatusRuntimeException e) {
            return new CatalogDTO();
        }
    }

}
