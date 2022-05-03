package ai.giskard.web.rest.controllers;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.RowFilter;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.DatasetService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tech.tablesaw.api.Row;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.DataFrameWriter;
import tech.tablesaw.io.json.JsonWriter;

import javax.validation.constraints.NotNull;
import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

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

    /**
     * Retrieve the row specified by the given index on the dataset
     *
     * @param datasetId id of the dataset
     * @return List of datasets
     */

    @GetMapping("/dataset/{datasetId}/rowsFiltered")
    public HashMap<String, String> getRowsFiltered(@PathVariable @NotNull Long datasetId,@RequestParam("modelId") @NotNull Long modelId, @RequestParam("threshold") @NotNull float threshold, @RequestParam("target") @NotNull String target, @RequestParam("filter") @NotNull RowFilter filter, @RequestParam("rangeMin") @NotNull int rangeMin, @RequestParam("rangeMax") @NotNull int rangeMax) throws IOException {
        Table filteredTable = datasetService.getRowsFiltered(datasetId,modelId, target, threshold, filter);
        Table filteredMTable=filteredTable.inRange(rangeMin, rangeMax);
        HashMap<String, String> map = new HashMap<>();
        map.put("data",  filteredMTable.write().toString("json"));
        map.put("rowNb",  ""+filteredTable.rowCount());
        return map;
    }

}
