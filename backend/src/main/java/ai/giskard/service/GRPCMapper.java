package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.worker.ArtifactRef;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class GRPCMapper {

    public ArtifactRef createRef(ProjectModel model) {
        return ArtifactRef.newBuilder().setProjectKey(model.getProject().getKey()).setId(model.getId().toString()).build();
    }

    public ArtifactRef createRef(Dataset ds, boolean sample) {
        return ArtifactRef.newBuilder()
            .setProjectKey(ds.getProject().getKey())
            .setId(ds.getId().toString())
            .setSample(sample)
            .build();
    }

}
