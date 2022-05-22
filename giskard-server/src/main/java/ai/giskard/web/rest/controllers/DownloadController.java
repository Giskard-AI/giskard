
package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.service.DownloadService;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.FileUploadService;
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
import java.nio.file.Path;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/files/")
public class DownloadController {
    final ModelRepository modelRepository;
    final DatasetRepository datasetRepository;
    final GiskardMapper giskardMapper;
    final DownloadService downloadService;
    final FileUploadService fileUploadService;
    final FileLocationService fileLocationService;

    /**
     * Download model file
     *
     * @param id model's id
     * @return model file
     * @throws IOException
     */
    @GetMapping("models/{id}")
    @Transactional
    public ResponseEntity<Resource>  downloadModel(@PathVariable @NotNull Long id) throws IOException {
        ProjectModel model = modelRepository.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT_MODEL, id));
        Path path = fileLocationService.resolvedModelPath(model.getProject().getKey(), model.getId());
        return downloadService.download(path, ".pkl");
    }

    /**
     *
     * @param id dataset's id
     * @return
     * @throws IOException
     */
    @GetMapping("datasets/{id}")
    @Transactional
    public ResponseEntity<Resource> downloadDataset(@PathVariable @NotNull Long id) throws IOException {
        Dataset dataset = datasetRepository.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, id));
        Path path = fileLocationService.resolvedDatasetPath(dataset.getProject().getKey(), dataset.getId());
        return downloadService.download(path, ".csv");
    }


}
