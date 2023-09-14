package ai.giskard.service.ml;

import ai.giskard.domain.Project;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.MLWorkerWSCatalogDTO;
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
import com.fasterxml.jackson.core.JsonProcessingException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

import static ai.giskard.ml.dto.MLWorkerWSUtils.convertMLWorkerWSObject;

@Service
@RequiredArgsConstructor
public class MLWorkerCacheService {

    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final TestFunctionService testFunctionService;
    private final TestFunctionRepository testFunctionRepository;
    private final SlicingFunctionService slicingFunctionService;
    private final SlicingFunctionRepository slicingFunctionRepository;
    private final TransformationFunctionService transformationFunctionService;
    private final TransformationFunctionRepository transformationFunctionRepository;
    private final ProjectRepository projectRepository;
    private final GiskardMapper giskardMapper;

    @Transactional
    public CatalogDTO getCatalog(long projectId) {
        // TODO: Remove from transaction, however it mostly relly on cache so impact is reduced

        Project project = projectRepository.getMandatoryById(projectId);
        findGiskardTest(project.isUsingInternalWorker());

        return CatalogDTO.builder()
            .tests(testFunctionRepository.findAll().stream().map(giskardMapper::toDTO).toList())
            .slices(slicingFunctionRepository.findAllForProject(project).stream()
                .map(giskardMapper::toDTO).toList())
            .transformations(transformationFunctionRepository.findAllForProject(project).stream()
                .map(giskardMapper::toDTO).toList())
            .build();
    }

    public void findGiskardTest(boolean isInternal) {
        if (isInternal) {
            return;
        }

        CatalogDTO catalogWithoutPickles = getTestFunctions(false);
        testFunctionService.saveAll(catalogWithoutPickles.getTests());
        slicingFunctionService.saveAll(catalogWithoutPickles.getSlices());
        transformationFunctionService.saveAll(catalogWithoutPickles.getTransformations());
    }

    private CatalogDTO getTestFunctions(boolean isInternal) {
        if (mlWorkerWSService.isWorkerConnected(isInternal ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL)) {
            MLWorkerWSCatalogDTO response;
            UUID replyUuid = mlWorkerWSCommService.performActionAsync(
                isInternal ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL,
                MLWorkerWSAction.GET_CATALOG, null
            );
            String reply = mlWorkerWSCommService.blockAwaitReply(replyUuid);
            if (reply != null) {
                try {
                    response = mlWorkerWSCommService.parseReplyDTO(reply, MLWorkerWSCatalogDTO.class);
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
                } catch (JsonProcessingException e) {
                    mlWorkerWSCommService.parseReplyErrorDTO(reply);
                }
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
