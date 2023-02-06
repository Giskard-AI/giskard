package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@UIModel
@Getter
@Setter
@NoArgsConstructor
public class PostImportProjectDTO {
    private Map<String, String> mappedUsers;
    private String projectKey;
    private String pathToMetadataDirectory;
}
