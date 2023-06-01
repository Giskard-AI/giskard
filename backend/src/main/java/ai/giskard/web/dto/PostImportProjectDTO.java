package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

import java.util.Map;

@UIModel
@Getter
@Setter
@AllArgsConstructor
public class PostImportProjectDTO {
    Map<String, String> mappedUsers;
    String projectKey;
    String pathToMetadataDirectory;
}
