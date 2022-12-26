package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import lombok.RequiredArgsConstructor;
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

    public Path resolvedDatasetPath(String projectKey, String datasetId) {
        return resolvedProjectHome(projectKey).resolve("datasets").resolve(createZSTname("data_", datasetId.toString()));
    }

    public Path resolvedModelPath(String projectKey, String modelId) {
        return modelsDirectory(projectKey).resolve(createZSTname("model_", modelId));
    }

    public Path resolvedInspectionPath(String projectKey, Long inspectionId) {
        return modelsDirectory(projectKey).resolve(Paths.get("inspections", inspectionId.toString()));
    }

    public Path resolvedProjectHome(String projectKey) {
        return giskardHome().resolve(projectHome(projectKey));
    }

    public Path giskardHome() {
        return applicationProperties.getHome();
    }

    public static String createZSTname(String prefix, String id) {
        return prefix + id + ".zst";
    }
}
