package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.MLWorkerWSBaseDTO;
import ai.giskard.ml.dto.MLWorkerWSCatalogDTO;
import ai.giskard.ml.tunnel.MLWorkerTunnelService;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.service.SlicingFunctionService;
import ai.giskard.service.TestFunctionService;
import ai.giskard.service.TransformationFunctionService;
import ai.giskard.web.dto.CatalogDTO;
import ai.giskard.web.dto.SlicingFunctionDTO;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.TransformationFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.stream.Stream;

import static ai.giskard.ml.dto.MLWorkerWSUtils.convertMLWorkerWSObject;

@Service
@RequiredArgsConstructor
public class MLWorkerCacheService {

    private final MLWorkerService mlWorkerService;
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final MLWorkerTunnelService mlWorkerTunnelService;
    private final TestFunctionService testFunctionService;
    private final TestFunctionRepository testFunctionRepository;
    private final SlicingFunctionService slicingFunctionService;
    private final SlicingFunctionRepository slicingFunctionRepository;
    private final TransformationFunctionService transformationFunctionService;
    private final TransformationFunctionRepository transformationFunctionRepository;
    private final ProjectRepository projectRepository;
    private final GiskardMapper giskardMapper;
    private CatalogDTO catalogWithoutPickles = new CatalogDTO();

    @Transactional
    public CatalogDTO getCatalog(long projectId) {
        // TODO: Remove from transaction, however it mostly relly on cache so impact is reduced
        CatalogDTO catalog = findGiskardTest(projectRepository.getMandatoryById(projectId).isUsingInternalWorker());

        return CatalogDTO.builder()
            .tests(Stream.concat(
                    testFunctionRepository.findAll().stream().map(giskardMapper::toDTO),
                    catalog.getTests().stream()
                )
                .toList())
            .slices(Stream.concat(
                    slicingFunctionRepository.findAll().stream().map(giskardMapper::toDTO),
                    catalog.getSlices().stream()
                )
                .toList())
            .transformations(Stream.concat(
                    transformationFunctionRepository.findAll().stream().map(giskardMapper::toDTO),
                    catalog.getTransformations().stream()
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
            slicingFunctionService.saveAll(catalogWithoutPickles.getSlices());
            transformationFunctionService.saveAll(catalogWithoutPickles.getTransformations());
            mlWorkerTunnelService.setClearCacheRequested(false);
        }

        return catalogWithoutPickles;
    }

    private CatalogDTO getTestFunctions(boolean isInternal) {
        if (mlWorkerWSService.isWorkerConnected(isInternal ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL)) {
            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                isInternal ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL,
                MLWorkerWSAction.getCatalog, null
            );
            if (result instanceof MLWorkerWSCatalogDTO response) {

                return CatalogDTO.builder()
                    .tests(response.getTests().values().stream()
                        .map(test -> convertMLWorkerWSObject(test, TestFunctionDTO.class))
                        .toList())
                    .slices(response.getSlices().values().stream()
                        .map(test -> convertMLWorkerWSObject(test, SlicingFunctionDTO.class))
                        .toList())
                    .transformations(response.getTransformations().values().stream()
                        .map(test -> convertMLWorkerWSObject(test, TransformationFunctionDTO.class))
                        .toList())
                    .build();
            }
        } else if (!isInternal) {
            // Fallback to internal ML worker to not display empty catalog
            CatalogDTO catalog = getTestFunctions(true);
            catalog.getTests().forEach(fn -> fn.setPotentiallyUnavailable(true));
            catalog.getSlices().forEach(fn -> fn.setPotentiallyUnavailable(true));
            catalog.getTransformations().forEach(fn -> fn.setPotentiallyUnavailable(true));
            return catalog;
        }
        return new CatalogDTO();
    }

}
