package ai.giskard.service;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ModelType;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
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
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Map;

import static ai.giskard.service.FileLocationService.createZSTname;

@Service
@RequiredArgsConstructor
public class FileUploadService {
    final ModelRepository modelRepository;
    final UserRepository userRepository;
    final GiskardMapper giskardMapper;

    final ProjectService projectService;
    final ProjectRepository projectRepository;
    private final FileLocationService locationService;
    private final DatasetRepository datasetRepository;

    private final Logger log = LoggerFactory.getLogger(FileUploadService.class);

    @Transactional
    public ProjectModel uploadModel(ModelUploadParamsDTO modelParams, InputStream modelStream, InputStream requirementsStream) throws IOException {
        Project project = projectRepository.getOneByKey(modelParams.getProjectKey());
        Path projectModelsPath = locationService.modelsDirectory(project.getKey());
        createOrEnsureOutputDirectory(projectModelsPath);

        ProjectModel model = createProjectModel(modelParams);

        // first save to get ID that will be used in the filenames
        ProjectModel savedModel = modelRepository.save(model);

        String modelFilename = createZSTname("model_", savedModel.getId());
        Path modelFilePath = projectModelsPath.resolve(modelFilename);
        long size = modelStream.transferTo(Files.newOutputStream(modelFilePath));
        model.setSize(size);
        model.setFileName(modelFilename);

        String requirementsFilename = String.format("model-requirements_%s.txt", savedModel.getId());
        Path requirementsFilePath = projectModelsPath.resolve(requirementsFilename);
        try {
            requirementsStream.transferTo(Files.newOutputStream(requirementsFilePath));
        } catch (IOException e) {
            throw new RuntimeException("Error writing requirements file: " + requirementsFilePath, e);
        }
        model.setRequirementsFileName(requirementsFilename);
        return modelRepository.save(model);
    }

    private ProjectModel createProjectModel(ModelUploadParamsDTO modelParams) {
        ProjectModel model = new ProjectModel();
        model.setName(nameOrDefault(modelParams.getName(), "Model"));
        model.setProject(projectRepository.getOneByKey(modelParams.getProjectKey()));
        model.setLanguageVersion(modelParams.getLanguageVersion());
        model.setLanguage(modelParams.getLanguage());
        model.setModelType(getModelType(modelParams));
        model.setThreshold(modelParams.getThreshold());
        model.setFeatureNames(modelParams.getFeatureNames());
        model.setClassificationLabels(modelParams.getClassificationLabels());
        return model;
    }

    private String nameOrDefault(String name, String entity) {
        if (name != null) {
            return name;
        }
        DateTimeFormatter dateTimeFormat = DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm.ss").withZone(ZoneId.systemDefault());
        return String.format("%s - %s", entity, dateTimeFormat.format(Instant.now()));
    }

    private ModelType getModelType(ModelUploadParamsDTO modelParams) {
        ModelType modelType;
        switch (modelParams.getModelType().toLowerCase().trim()) {
            case "classification":
                if (modelParams.getClassificationLabels().size() > 2) {
                    modelType = ModelType.MULTICLASS_CLASSIFICATION;
                } else {
                    modelType = ModelType.BINARY_CLASSIFICATION;
                }
                break;
            case "regression":
                modelType = ModelType.REGRESSION;
                break;
            default:
                throw new IllegalArgumentException("Invalid model type: %s, supported values are \"classification\" or \"regression\"");
        }
        return modelType;
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

    @Transactional
    public Dataset uploadDataset(Project project, String datasetName, Map<String, FeatureType> featureTypes, String target, InputStream inputStream) throws IOException {
        Path datasetPath = locationService.datasetsDirectory(project.getKey());
        createOrEnsureOutputDirectory(datasetPath);

        Dataset dataset = new Dataset();
        dataset.setName(nameOrDefault(datasetName, "Dataset"));
        dataset.setProject(project);
        dataset.setFeatureTypes(featureTypes);
        dataset.setTarget(target);
        dataset = datasetRepository.save(dataset);

        String fileName = createZSTname("data_", dataset.getId());
        dataset.setFileName(fileName);
        long size = inputStream.transferTo(Files.newOutputStream(datasetPath.resolve(fileName)));
        dataset.setSize(size);

        return datasetRepository.save(dataset);
    }
}
