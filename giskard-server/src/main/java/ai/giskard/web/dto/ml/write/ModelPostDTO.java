package ai.giskard.web.dto.ml.write;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class ModelPostDTO extends FilePostDTO {

    @JsonProperty("python_version")
    private String pythonVersion;

}
