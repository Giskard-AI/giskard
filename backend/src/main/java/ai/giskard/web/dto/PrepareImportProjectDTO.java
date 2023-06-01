package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Set;

@UIModel
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class PrepareImportProjectDTO {
    private boolean projectKeyAlreadyExists;
    private Set<String> loginsImportedProject;
    private Set<String> loginsCurrentInstance;
    private String projectKey;
    private String temporaryMetadataDirectory;
}
