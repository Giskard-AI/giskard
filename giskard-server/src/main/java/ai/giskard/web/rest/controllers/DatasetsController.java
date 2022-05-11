package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.DatasetService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tech.tablesaw.api.Table;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class DatasetsController {

    private final DatasetRepository datasetRepository;
    private final GiskardMapper giskardMapper;
    private final DatasetService datasetService;

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

    /**
     * Get the rows in the specified range
     *
     * @param datasetId id of the dataset
     * @return List of datasets
     */

    @GetMapping("/dataset/{datasetId}/rows")
    public String getRows(@PathVariable @NotNull Long datasetId, @RequestParam("rangeMin") @NotNull int rangeMin, @NotNull int rangeMax) throws IOException {
        Table filteredTable = datasetService.getRows(datasetId, rangeMin, rangeMax);
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
    public DatasetDetailsDTO datasetDetails(@PathVariable @NotNull Long datasetId) {
        return datasetService.getDetails(datasetId);
    }
}
