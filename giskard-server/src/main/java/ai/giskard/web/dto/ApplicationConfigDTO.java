package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Builder;
import lombok.Getter;

@UIModel
@Getter
@Builder
public class ApplicationConfigDTO {
    private String giskardVersion;
}
