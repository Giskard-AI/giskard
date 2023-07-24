package ai.giskard.web.dto;

import ai.giskard.worker.ArtifactRef;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@UIModel
public class ArtifactRefDTO {
    private String id;
    private String projectKey;

    public ArtifactRefDTO(ArtifactRef artifactRef) {
        this.id = artifactRef.getId();
        this.projectKey = artifactRef.getProjectKey();
    }
}
