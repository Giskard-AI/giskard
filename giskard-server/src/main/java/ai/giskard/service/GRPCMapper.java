package ai.giskard.service;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.worker.SerializedGiskardDataset;
import ai.giskard.worker.SerializedGiskardModel;
import com.google.common.collect.Maps;
import com.google.protobuf.ByteString;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
@RequiredArgsConstructor
public class GRPCMapper {
    private final FileLocationService locationService;

    public SerializedGiskardModel serialize(ProjectModel model) throws IOException {
        Path modelPath = locationService.resolvedModelPath(model.getProject().getKey(), model.getId());

        SerializedGiskardModel.Builder builder = SerializedGiskardModel.newBuilder()
            .setSerializedPredictionFunction(ByteString.readFrom(Files.newInputStream(modelPath)))
            .setModelType(model.getModelType().getSimplifiedName());
        if (model.getThreshold() != null) {
            builder.setThreshold(model.getThreshold());
        }
        if (model.getClassificationLabels() != null) {
            builder.addAllClassificationLabels(model.getClassificationLabels());
        }
        if (model.getFeatureNames() != null) {
            builder.addAllFeatureNames(model.getFeatureNames());
        }
        return builder.build();
    }

    public SerializedGiskardDataset serialize(Dataset dataset) throws IOException {
        Path datasetPath = locationService.resolvedDatasetPath(dataset.getProject().getKey(), dataset.getId());

        SerializedGiskardDataset.Builder builder = SerializedGiskardDataset.newBuilder()
            .setSerializedDf(ByteString.readFrom(Files.newInputStream(datasetPath)))
            .putAllFeatureTypes(Maps.transformValues(dataset.getFeatureTypes(), FeatureType::getName));
        if (dataset.getTarget() != null) {
            builder.setTarget(dataset.getTarget());
        }
        return builder.build();
    }
}
