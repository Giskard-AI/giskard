package ai.giskard.web.rest.controllers;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.GiskardRuntimeException;
import ai.giskard.service.ProjectService;
import ai.giskard.utils.GSKFileUtils;
import ai.giskard.utils.GiskardStringUtils;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Path;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/download")
public class DownloadController {
    private final FileLocationService fileLocationService;
    private final ModelRepository modelRepository;
    private final DatasetRepository datasetRepository;
    private final PermissionEvaluator permissionEvaluator;
    private final ProjectService projectService;
    private final ProjectRepository projectRepository;

    @GetMapping("/model/{modelId}")
    @Transactional
    public ResponseEntity<InputStreamResource> downloadModel(@PathVariable("modelId") UUID modelId) throws IOException {
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());

        Path path = fileLocationService.resolvedModelPath(model);
        String name = "giskard_model_" + (model.getName() != null ? model.getName() : model.getId());
        return createDecompressedStreamResponse(path, name);
    }

    @GetMapping("/dataset/{id}")
    @Transactional
    public ResponseEntity<InputStreamResource> downloadDataset(@PathVariable("id") UUID datasetId) throws IOException {
        Dataset dataset = datasetRepository.getById(datasetId);
        permissionEvaluator.validateCanReadProject(dataset.getProject().getId());

        Path path = fileLocationService.resolvedDatasetPath(dataset);
        String name = "giskard_dataset_" + (dataset.getName() != null ? dataset.getName() : dataset.getId());
        return createDecompressedStreamResponse(path, name);
    }

    @GetMapping("/project/{id}/export")
    @Transactional
    public @ResponseBody ResponseEntity<byte[]> exportProject(@PathVariable("id") Long id) throws IOException {
            Project project = this.projectRepository.findById(id).orElseThrow(() -> new GiskardRuntimeException("Could not find your project in the database"));
            permissionEvaluator.canReadProject(id);
            byte[] zFile = this.projectService.export(id);
            HttpHeaders resHeaders = new HttpHeaders();
            resHeaders.setContentType(MediaType.APPLICATION_OCTET_STREAM);
            resHeaders.setContentDispositionFormData("attachment", GiskardStringUtils.toSlug(project.getKey()) + ".zip");
            return new ResponseEntity<>(zFile, resHeaders ,HttpStatus.OK);
    }

    private ResponseEntity<InputStreamResource> createDecompressedStreamResponse(Path path, String name) throws IOException {

        try (ByteArrayOutputStream baos = GSKFileUtils.createZipArchive(path.toAbsolutePath().toString())) {
            InputStreamResource isr = new InputStreamResource(new ByteArrayInputStream(baos.toByteArray()));

            HttpHeaders respHeaders = new HttpHeaders();
            respHeaders.setContentType(MediaType.APPLICATION_OCTET_STREAM);
            respHeaders.setContentDispositionFormData("attachment", GiskardStringUtils.toSlug(name) + ".zip");

            return new ResponseEntity<>(isr, respHeaders, HttpStatus.OK);
        }

    }


}
