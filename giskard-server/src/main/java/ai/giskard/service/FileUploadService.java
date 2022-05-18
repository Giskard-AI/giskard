package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.web.dto.ModelUploadParamsDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.compress.compressors.CompressorException;
import org.apache.commons.compress.compressors.CompressorStreamFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;

import static ai.giskard.service.FileLocationService.createZSTname;

@Service
@RequiredArgsConstructor
public class FileUploadService {
    final ModelRepository modelRepository;
    final GiskardMapper giskardMapper;

    final ProjectService projectService;
    final ProjectRepository projectRepository;
    private final FileLocationService locationService;
    private final DatasetRepository datasetRepository;

    private final Logger log = LoggerFactory.getLogger(FileUploadService.class);

    @Transactional
    public ProjectModel uploadModel(ModelUploadParamsDTO modelParams, InputStream modelStream, InputStream requirementsStream) {
        Project project = projectRepository.getOneByKey(modelParams.getProjectKey());
        Path projectModelsPath = locationService.modelsDirectory(project.getKey());
        createOrEnsureOutputDirectory(projectModelsPath);

        ProjectModel model = giskardMapper.modelUploadParamsDTOtoProjectModel(modelParams);
        model.setProject(project);
        // first save to get ID that will be used in the filenames
        ProjectModel savedModel = modelRepository.save(model);

        String modelFilename = createZSTname("model_", savedModel.getId());
        Path modelFilePath = projectModelsPath.resolve(modelFilename);
        try {
            modelStream.transferTo(Files.newOutputStream(modelFilePath));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        model.setFileName(modelFilename);

        String requirementsFilename = createZSTname("model-requirements_", savedModel.getId());
        Path requirementsFilePath = projectModelsPath.resolve(requirementsFilename);
        try {
            requirementsStream.transferTo(Files.newOutputStream(requirementsFilePath));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        model.setRequirementsFileName(requirementsFilename);
        return modelRepository.save(model);
    }

    private void createOrEnsureOutputDirectory(Path outputPath) {
        if (Files.exists(outputPath) && !Files.isDirectory(outputPath)) {
            throw new RuntimeException(String.format("Output path exists, but not a directory: %s", outputPath));
        }
        try {
            Files.createDirectories(outputPath);
        } catch (IOException e) {
            throw new RuntimeException("Failed to create output directory", e);
        }
    }

    public InputStream decompressFileToStream(Path compressedInputPath) {
        log.info("Decompressing file {}", compressedInputPath);
        try {
            final InputStream compressedInputStream = Files.newInputStream(compressedInputPath);
            return new CompressorStreamFactory()
                .createCompressorInputStream(CompressorStreamFactory.ZSTANDARD, compressedInputStream);
        } catch (IOException e) {
            throw new RuntimeException(String.format("Failed to read file to %s", compressedInputPath), e);
        } catch (CompressorException e) {
            throw new RuntimeException(String.format("Failed to decompress input when reading %s", compressedInputPath), e);
        }
    }

    @PreAuthorize("@permissionEvaluator.canWriteProject( #project.id)")
    @Transactional
    public Dataset uploadDataset(Project project, String datasetName, InputStream inputStream) {
        Path datasetPath = locationService.datasetsDirectory(project.getKey());
        createOrEnsureOutputDirectory(datasetPath);

        Dataset dataset = new Dataset();
        dataset.setName(datasetName);
        dataset.setProject(project);
        dataset = datasetRepository.save(dataset);

        String fileName = createZSTname("data_", dataset.getId());
        dataset.setFileName(fileName);
        try {
            inputStream.transferTo(Files.newOutputStream(datasetPath.resolve(fileName)));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        return datasetRepository.save(dataset);
    }
}
