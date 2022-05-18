
package ai.giskard.web.rest.controllers;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.service.DownloadService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.io.IOException;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/files/")
public class DownloadController {
    final ModelRepository modelRepository;
    final DatasetRepository datasetRepository;
    final GiskardMapper giskardMapper;
    final ApplicationProperties applicationProperties;
    final DownloadService downloadService;

    @GetMapping("models/{id}")
    @Transactional
    public ResponseEntity<Resource> downloadModel(@PathVariable @NotNull Long id) throws IOException {
        ProjectModel model = modelRepository.findById(id).orElseThrow(()->new EntityNotFoundException(Entity.PROJECT_MODEL, id));
        //TODO adapt with LocationService
        String path = applicationProperties.getBucketPath() + "/files-bucket" + "/" + model.getProject().getKey() + "/" + model.getFileName() + ".zst";
        return downloadService.download(path);
    }

    @GetMapping("datasets/{id}")
    @Transactional
    public ResponseEntity<Resource> downloadDataset(@PathVariable @NotNull Long id) throws IOException {
        Dataset dataset = datasetRepository.findById(id).orElseThrow(()->new EntityNotFoundException(Entity.DATASET, id));
        String path = applicationProperties.getBucketPath() + "/files-bucket" + "/" + dataset.getProject().getKey() + "/" + dataset.getFileName() + ".zst";
        return downloadService.download(path);
    }

}
