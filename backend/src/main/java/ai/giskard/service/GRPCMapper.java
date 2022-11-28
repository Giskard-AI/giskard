package ai.giskard.service;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.worker.SerializedGiskardDataset;
import ai.giskard.worker.SerializedGiskardModel;
import com.google.common.collect.Maps;
import com.google.protobuf.DoubleValue;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class GRPCMapper {

    public SerializedGiskardModel serialize(ProjectModel model) {
        SerializedGiskardModel.Builder builder = SerializedGiskardModel.newBuilder()
            .setFileName(model.getFileName())
            .setProjectKey(model.getProject().getKey())
            .setModelType(model.getModelType().getSimplifiedName());
        if (model.getThreshold() != null) {
            builder.setThreshold(DoubleValue.newBuilder().setValue(model.getThreshold()).build());
        }
        if (model.getClassificationLabels() != null) {
            builder.addAllClassificationLabels(model.getClassificationLabels());
        }
        if (model.getFeatureNames() != null) {
            builder.addAllFeatureNames(model.getFeatureNames());
        }
        return builder.build();
    }

    public SerializedGiskardDataset serialize(Dataset dataset) {
        SerializedGiskardDataset.Builder builder = SerializedGiskardDataset.newBuilder()
            .setFileName(dataset.getFileName())
            .setProjectKey(dataset.getProject().getKey())
            .putAllFeatureTypes(Maps.transformValues(dataset.getFeatureTypes(), FeatureType::getName));
        if (dataset.getColumnTypes() != null) {
            builder.putAllColumnTypes(dataset.getColumnTypes());

        }
        if (dataset.getTarget() != null) {
            builder.setTarget(dataset.getTarget());
        }
        return builder.build();
    }
}
