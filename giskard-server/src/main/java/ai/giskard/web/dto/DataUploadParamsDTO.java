package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@UIModel
@Getter
@Setter
@NoArgsConstructor
public class DataUploadParamsDTO {
    private String name;
    private String projectKey;
}
