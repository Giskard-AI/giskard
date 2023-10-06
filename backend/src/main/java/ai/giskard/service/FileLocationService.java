package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.RandomStringUtils;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

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

    public Path resolvedDatasetPath(Dataset dataset) {
        return resolvedDatasetPath(dataset.getProject().getKey(), dataset.getId());
    }

    public Path resolvedDatasetPath(String projectKey, UUID datasetId) {
        return datasetsDirectory(projectKey).resolve(datasetId.toString());
    }

    public Path temporaryMetadataDirectory(String prefix) {
        String randomDirName = RandomStringUtils.randomAlphanumeric(8).toLowerCase(); // NOSONAR: no security risk here
        return resolvedTmpPath().resolve(prefix + "-" + randomDirName);
    }

    public Path resolvedMetadataPath(Path temporaryMetadataDir, String entityName) {
        return temporaryMetadataDir.resolve(entityName.toLowerCase() + "-metadata.yaml");
    }

    public Path resolvedSlicePath(String projectKey, UUID datasetId, String sliceHash) {
        return slicesDirectory(projectKey).resolve("slice_" + datasetId.toString() + "_" + sliceHash + ".slice");
    }

    public Path resolvedModelPath(ProjectModel model) {
        return resolvedModelPath(model.getProject().getKey(), model.getId());
    }

    public Path resolvedModelPath(String projectKey, UUID modelId) {
        return modelsDirectory(projectKey).resolve(modelId.toString());
    }

    public Path resolvedInspectionPath(String projectKey, Long inspectionId) {
        return modelsDirectory(projectKey).resolve(Paths.get("inspections", inspectionId.toString()));
    }

    public Path resolvedProjectHome(String projectKey) {
        return giskardHome().resolve(projectHome(projectKey));
    }

    public Path globalPath() {
        return giskardHome().resolve(projectHome("global"));
    }

    public Path resolvedTmpPath() {
        return giskardHome().resolve("tmp");
    }

    public Path licensePath() {
        return giskardHome().resolve("license.lic");
    }

    public Path giskardHome() {
        return applicationProperties.getHome();
    }

    public static String createZSTname(String prefix, UUID id) {
        return prefix + id.toString() + ".zst";
    }

    public static String createTXTname(String prefix, UUID id) {
        return prefix + id.toString() + ".txt";
    }

}
