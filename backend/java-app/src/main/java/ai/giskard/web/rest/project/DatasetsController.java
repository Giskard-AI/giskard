package ai.giskard.web.rest.project;

import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.dto.ml.DatasetDTO;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v2/project/datasets")
public class DatasetsController {
    private DatasetRepository datasetRepository;

    public DatasetsController(DatasetRepository modelRepository) {
        this.datasetRepository = modelRepository;
    }

    @GetMapping("")
    public List<DatasetDTO> listProjectDatasets(@RequestParam @NotNull Long projectId) {
        return datasetRepository.findAllByProjectId(projectId).stream().map(DatasetDTO::new).collect(Collectors.toList());
    }
}
