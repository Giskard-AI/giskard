package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.dto.ml.DatasetDTO;
import ai.giskard.service.mapper.GiskardMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;

@RestController
@RequestMapping("/api/v2/")
public class DatasetsController {

    private DatasetRepository datasetRepository;
    private GiskardMapper giskardMapper;


    public DatasetsController(DatasetRepository datasetRepository, GiskardMapper giskardMapper) {
        this.datasetRepository = datasetRepository;
        this.giskardMapper = giskardMapper;
    }

    /**
     * Retrieve the list of datasets from the specified project
     * Returns all the project's datasets if the user is admin, project's owner or in project's guest list
     *
     * @param projectId id of the project
     * @return List of datasets
     */
    @GetMapping("project/{projectId}/datasets")
    public List<DatasetDTO> listProjectDatasets(@PathVariable @NotNull Long projectId) {
        return giskardMapper.datasetsToDatasetDTOs(this.datasetRepository.findAllByProjectId(projectId));
    }
}
