package ai.giskard.web.rest.controllers;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.FileUploadService;
import ai.giskard.web.dto.DataUploadParamsDTO;
import ai.giskard.web.dto.ModelUploadParamsDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.ModelDTO;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class UploadController {
    private final GiskardMapper giskardMapper;
    private final FileUploadService uploadService;
    private final ProjectRepository projectRepository;
    private final PermissionEvaluator permissionEvaluator;
    private final Logger log = LoggerFactory.getLogger(UploadController.class);

    @PostMapping("project/models/upload")
    @Transactional
    public ModelDTO uploadModel(
        @RequestPart("metadata") ModelUploadParamsDTO params,
        @RequestPart("modelFile") MultipartFile modelFile,
        @RequestPart("requirementsFile") MultipartFile requirementsFile) throws IOException {
        log.info("Loading model: {}.{} into project {}", params.getProjectKey(), params.getName(), params.getProjectKey());

        ProjectModel savedModel = uploadService.uploadModel(params, modelFile.getInputStream(), requirementsFile.getInputStream());
        return giskardMapper.modelToModelDTO(savedModel);
    }

    @PostMapping("project/data/upload")
    @Transactional
    public DatasetDTO dataUpload(
        @RequestPart("metadata") DataUploadParamsDTO params,
        @RequestPart("file") MultipartFile file) throws IOException {
        log.info("Loading dataset: {}.{} into project {}", params.getProjectKey(), params.getName(), params.getProjectKey());

        Project project = projectRepository.getOneByKey(params.getProjectKey());
        permissionEvaluator.validateCanWriteProject(project.getId());

        Dataset savedDataset = uploadService.uploadDataset(
            project, params.getName(), params.getFeatureTypes(),
            params.getTarget(), file.getInputStream()
        );
        return giskardMapper.datasetToDatasetDTO(savedDataset);
    }

}
