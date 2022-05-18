package ai.giskard.service;

import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.worker.DataFrame;
import ai.giskard.worker.DataRow;
import ai.giskard.worker.RunModelForDataFrameResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

@Service
@Transactional
@RequiredArgsConstructor
public class ModelService {
    private final MLWorkerService mlWorkerService;
    private final FileLocationService locationService;

    public RunModelForDataFrameResponse predict(ProjectModel model, Map<String, String> features) {
        Path modelPath = locationService.resolvedModelPath(model.getProject().getKey(), model.getId());
        RunModelForDataFrameResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.runModelForDataframe(
                Files.newInputStream(modelPath),
                DataFrame.newBuilder().addRows(DataRow.newBuilder().putAllFeatures(features)).build());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return response;


    }
}
