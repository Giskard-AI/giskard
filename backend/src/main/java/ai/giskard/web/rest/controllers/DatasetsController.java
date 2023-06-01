package ai.giskard.web.rest.controllers;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.DatasetService;
import ai.giskard.service.GiskardRuntimeException;
import ai.giskard.service.ProjectFileDeletionService;
import ai.giskard.service.UsageService;
import ai.giskard.web.dto.FeatureMetadataDTO;
import ai.giskard.web.dto.MessageDTO;
import ai.giskard.web.dto.PrepareDeleteDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import tech.tablesaw.api.Table;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.util.List;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class DatasetsController {

    private final DatasetRepository datasetRepository;
    private final GiskardMapper giskardMapper;
    private final DatasetService datasetService;
    private final ProjectRepository projectRepository;
    private final ProjectFileDeletionService deletionService;
    private final UsageService usageService;

    /**
     * Retrieve the list of datasets from the specified project
     * Returns all the project's datasets if the user is admin, project's owner or in project's guest list
     *
     * @param projectId id of the project
     * @return List of datasets
     */
    @GetMapping("project/{projectId}/datasets")
    public List<DatasetDTO> listProjectDatasets(@PathVariable @NotNull Long projectId) {
        return giskardMapper.datasetsToDatasetDTOs(datasetRepository.findAllByProjectId(projectId));
    }

    @GetMapping("project/{projectKey}/datasets/{datasetId}")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    @Transactional
    public DatasetDTO getDatasetMeta(@PathVariable("projectKey") @NotNull String projectKey,
                                     @PathVariable("datasetId") @NotNull UUID datasetId) {
        return giskardMapper.datasetToDatasetDTO(datasetRepository.getById(datasetId));
    }


    /**
     * Get the rows in the specified range
     *
     * @param datasetId id of the dataset
     * @return List of datasets
     */

    @GetMapping("/dataset/{datasetId}/rows")
    public String getRows(@PathVariable @NotNull UUID datasetId, @NotNull int offset, @NotNull int size) {
        Table filteredTable = datasetService.getRows(datasetId, offset, offset + size);
        return filteredTable.write().toString("json");
    }

    /**
     * Getting dataset's details, like number of rows, headers..
     * TODO add the headers
     *
     * @param datasetId
     * @return
     * @throws IOException
     */
    @GetMapping("/dataset/{datasetId}/details")
    public DatasetDetailsDTO datasetDetails(@PathVariable @NotNull UUID datasetId) {
        return datasetService.getDetails(datasetId);
    }

    @DeleteMapping("/dataset/{datasetId}")
    public MessageDTO deleteDataset(@PathVariable @NotNull UUID datasetId) {
        deletionService.deleteDataset(datasetId);
        return new MessageDTO("Dataset {} has been deleted", datasetId);
    }

    @GetMapping("/dataset/prepare-delete/{datasetId}")
    public PrepareDeleteDTO prepareDatasetDelete(@PathVariable @NotNull UUID datasetId) {
        return usageService.prepareDeleteDataset(datasetId);
    }

    @GetMapping("/dataset/{datasetId}/features")
    public List<FeatureMetadataDTO> datasetFeaturesMetadata(@PathVariable @NotNull UUID datasetId) {
        return datasetService.getFeaturesWithDistinctValues(datasetId);
    }

    @PostMapping("project/{projectKey}/datasets")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    @Transactional
    public void createDatasetMeta(@PathVariable("projectKey") @NotNull String projectKey, @RequestBody @NotNull DatasetDTO dto) {
        Project project = projectRepository.getOneByKey(projectKey);
        if (datasetRepository.existsById(dto.getId())) {
            throw new GiskardRuntimeException(String.format("Dataset already exists %s", dto.getId()));
        }
        Dataset dataset = giskardMapper.fromDTO(dto);
        dataset.setProject(project);
        datasetRepository.save(dataset);
    }
}
