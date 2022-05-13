package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.nio.file.Paths;

@Service
@RequiredArgsConstructor
public class FileLocationService {

    private final ApplicationProperties applicationProperties;

    public static Path modelRelativePath(ProjectModel model) {
        return Paths.get("projects", model.getProject().getKey(), "models").resolve(model.getFileName());
    }

    public static Path datasetRelativePath(Dataset dataset) {
        return Paths.get("projects", dataset.getProject().getKey(), "datasets").resolve(dataset.getFileName());
    }

    public Path modelsDirectory(String projectKey) {
        return resolvedProjectHome(projectKey).resolve("models");
    }

    public static Path projectHome(String projectKey) {
        return Paths.get("projects", projectKey);
    }

    public Path datasetsDirectory(String projectKey) {
        return resolvedProjectHome(projectKey).resolve("datasets");
    }

    private Path resolvedProjectHome(String projectKey) {
        return giskardHome().resolve(projectHome(projectKey));
    }

    private Path giskardHome() {
        return applicationProperties.getGiskardHome();
    }

}
