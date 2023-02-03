package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ProjectFile;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.RandomStringUtils;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.nio.file.Paths;

@Service
@RequiredArgsConstructor
public class FileLocationService {
    private final ApplicationProperties applicationProperties;

    public Path modelsDirectory(String projectKey) {
        return resolvedProjectHome(projectKey).resolve("models");
    }

    public static Path projectHome(String projectKey) {
        return Paths.get("projects", projectKey);
    }

    public Path datasetsDirectory(String projectKey) {
        return resolvedProjectHome(projectKey).resolve("datasets");
    }

    public Path slicesDirectory(String projectKey) {
        return resolvedProjectHome(projectKey).resolve("slices");
    }

    public Path resolvedDatasetPath(String projectKey, Long datasetId) {
        return resolvedProjectHome(projectKey).resolve("datasets").resolve(createZSTname("data_", datasetId));
    }

    public Path resolvedModelPath(String projectKey, Long modelId) {
        return modelsDirectory(projectKey).resolve(createZSTname("model_", modelId));
    }

    public Path temporaryMetadataDirectory(String prefix) {
        String randomDirName = RandomStringUtils.randomAlphanumeric(8).toLowerCase(); // NOSONAR: no security risk here
        return resolvedTmpPath().resolve(prefix + "-" + randomDirName);
    }

    public Path resolvedMetadataPath(Path temporaryMetadataDir, String entityName) {
        return temporaryMetadataDir.resolve(entityName.toLowerCase() + "-metadata.yaml");
    }

    public Path resolvedSlicePath(String projectKey, Long datasetId, String sliceHash) {
        return slicesDirectory(projectKey).resolve("slice_" + datasetId.toString() + "_" + sliceHash + ".slice");
    }

    public Path resolveFilePath(ProjectFile file) {
        String projectKey = file.getProject().getKey();
        if (file instanceof ProjectModel) {
            return resolvedModelPath(projectKey, file.getId());
        } else if (file instanceof Dataset) {
            return resolvedDatasetPath(projectKey, file.getId());
        } else {
            throw new IllegalArgumentException("Unknown file type");
        }
    }


    public Path resolvedInspectionPath(String projectKey, Long inspectionId) {
        return modelsDirectory(projectKey).resolve(Paths.get("inspections", inspectionId.toString()));
    }

    public Path resolvedProjectHome(String projectKey) {
        return giskardHome().resolve(projectHome(projectKey));
    }

    public Path resolvedTmpPath() {
        return giskardHome().resolve("tmp");
    }

    private Path giskardHome() {
        return applicationProperties.getHome();
    }

    public static String createZSTname(String prefix, Long id) {
        return prefix + id.toString() + ".zst";
    }

    public static String createTXTname(String prefix, Long id) {
        return prefix + id.toString() + ".txt";
    }

}
