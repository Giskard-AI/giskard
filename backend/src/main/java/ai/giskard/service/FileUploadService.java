package ai.giskard.service;

import ai.giskard.domain.ArtifactType;
import ai.giskard.domain.FeatureType;
import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ModelType;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.web.dto.ModelUploadParamsDTO;
import lombok.RequiredArgsConstructor;
import org.apache.commons.compress.compressors.CompressorException;
import org.apache.commons.compress.compressors.CompressorStreamFactory;
import org.apache.commons.io.FileUtils;
import org.apache.commons.io.IOUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.*;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static ai.giskard.service.FileLocationService.createZSTname;

@Service
@RequiredArgsConstructor
public class FileUploadService {
    private final ModelRepository modelRepository;
    private final ProjectRepository projectRepository;
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
        //model.setFileName(modelFilename);

        String requirementsFilename = String.format("model-requirements_%s.txt", savedModel.getId());
        Path requirementsFilePath = projectModelsPath.resolve(requirementsFilename);
        try {
            requirementsStream.transferTo(Files.newOutputStream(requirementsFilePath));
        } catch (IOException e) {
            throw new GiskardRuntimeException("Error writing requirements file: " + requirementsFilePath, e);
        }
        //model.setRequirementsFileName(requirementsFilename);
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
            case "classification" -> {
                modelType = ModelType.REGRESSION;
            }
            case "regression" -> modelType = ModelType.REGRESSION;
            default ->
                throw new IllegalArgumentException("Invalid model type: %s, supported values are \"classification\" or \"regression\"");
        }
        return modelType;
    }

    private void createOrEnsureOutputDirectory(Path outputPath) {
        if (Files.exists(outputPath) && !Files.isDirectory(outputPath)) {
            throw new GiskardRuntimeException(String.format("Output path exists, but not a directory: %s", outputPath));
        }
        try {
            Files.createDirectories(outputPath);
        } catch (IOException e) {
            throw new GiskardRuntimeException("Failed to create output directory", e);
        }
    }

    public InputStream decompressFileToStream(Path compressedInputPath) {
        log.info("Decompressing file {}", compressedInputPath);
        try {
            final InputStream compressedInputStream = Files.newInputStream(compressedInputPath);
            return new CompressorStreamFactory().createCompressorInputStream(CompressorStreamFactory.ZSTANDARD, compressedInputStream);
        } catch (IOException e) {
            throw new GiskardRuntimeException(String.format("Failed to read file to %s", compressedInputPath), e);
        } catch (CompressorException e) {
            throw new GiskardRuntimeException(String.format("Failed to decompress input when reading %s", compressedInputPath), e);
        }
    }

    @Transactional
    public Dataset uploadDataset(Project project, String datasetName, Map<String, FeatureType> featureTypes, Map<String, String> columnTypes, String target, InputStream inputStream) throws IOException {
        Path datasetPath = locationService.datasetsDirectory(project.getKey());
        createOrEnsureOutputDirectory(datasetPath);

        Dataset dataset = new Dataset();
        dataset.setName(nameOrDefault(datasetName, "Dataset"));
        dataset.setProject(project);
        dataset.setFeatureTypes(featureTypes);
        dataset.setColumnTypes(columnTypes);
        dataset.setTarget(target);
        dataset = datasetRepository.save(dataset);

        String fileName = createZSTname("data_", dataset.getId().toString());
        long size = inputStream.transferTo(Files.newOutputStream(datasetPath.resolve(fileName)));

        return datasetRepository.save(dataset);
    }

    public void saveArtifact(InputStream uploadedStream, String projectKey, ArtifactType artifactType, String artifactId, String path) throws IOException {
        Path artifactDirectory = locationService.resolvedProjectHome(projectKey).resolve(Path.of(artifactType.name(), artifactId));
        Path artifactPath = artifactDirectory.resolve(path);
        Path tempFile = artifactPath.resolveSibling(artifactPath.getFileName() + ".tmp");

        if (!artifactPath.normalize().startsWith(artifactDirectory.normalize())) {
            throw new GiskardRuntimeException(String.format("Artifact path %s isn't relative to artifact directory", path));
        }
        if (artifactPath.toFile().exists()) {
            throw new FileAlreadyExistsException(locationService.giskardHome().relativize(artifactPath).toString());
        }
        FileUtils.forceMkdirParent(artifactPath.toFile());
        FileUtils.deleteQuietly(tempFile.toFile());

        try (OutputStream out = new FileOutputStream(tempFile.toFile())) {
            IOUtils.copy(uploadedStream, out);
        }
        Files.move(tempFile, artifactPath);
    }

    public Set<String> listArtifacts(String projectKey, ArtifactType artifactType, String artifactId) throws IOException {
        Path artifactDirectory = locationService.resolvedProjectHome(projectKey).resolve(Path.of(artifactType.name(), artifactId));
        return FileUtils.listFiles(artifactDirectory.toFile(), null, true).stream()
            .map(file -> artifactDirectory.relativize(file.toPath()).toString())
            .collect(Collectors.toSet());
        //try (Stream<Path> stream = Files.list(artifactDirectory)) {
        //    return stream
        //        .filter(file -> !Files.isDirectory(file))
        //        .map(Path::getFileName)
        //        .map(Path::toString)
        //        .collect(Collectors.toSet());
        //}
    }

    public InputStream getArtifactStream(String projectKey, ArtifactType artifactType, String artifactId, String path) throws FileNotFoundException {
        Path artifactDirectory = locationService.resolvedProjectHome(projectKey).resolve(Path.of(artifactType.name(), artifactId));
        Path artifactPath = artifactDirectory.resolve(path);
        return new FileInputStream(artifactPath.toFile());
    }
}
