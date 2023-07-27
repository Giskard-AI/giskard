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

    public Path modelsDirectory() {
        return resolvedArtifactsDirectory().resolve("models");
    }

    public static Path projectHome(String projectKey) {
        return Paths.get("projects", projectKey);
    }

    public Path datasetsDirectory() {
        return resolvedArtifactsDirectory().resolve("datasets");
    }

    public Path resolvedDatasetPath(Dataset dataset) {
        return resolvedDatasetPath(dataset.getId());
    }

    public Path resolvedDatasetPath(UUID datasetId) {
        return datasetsDirectory().resolve(datasetId.toString());
    }

    public Path temporaryMetadataDirectory(String prefix) {
        String randomDirName = RandomStringUtils.randomAlphanumeric(8).toLowerCase(); // NOSONAR: no security risk here
        return resolvedTmpPath().resolve(prefix + "-" + randomDirName);
    }

    public Path resolvedMetadataPath(Path temporaryMetadataDir, String entityName) {
        return temporaryMetadataDir.resolve(entityName.toLowerCase() + "-metadata.yaml");
    }

    public Path resolvedModelPath(ProjectModel model) {
        return resolvedModelPath(model.getId());
    }

    public Path resolvedModelPath(UUID modelId) {
        return modelsDirectory().resolve(modelId.toString());
    }

    public Path resolvedInspectionPath(Long inspectionId) {
        return modelsDirectory().resolve(Paths.get("inspections", inspectionId.toString()));
    }

    public Path resolvedArtifactsDirectory() {
        return giskardHome().resolve("artifacts");
    }

    // TODO: remove all usage and delete
    public Path resolvedProjectHome(String projectKey) {
        return giskardHome().resolve(projectHome(projectKey));
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


}
