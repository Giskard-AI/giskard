package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@UIModel
@NoArgsConstructor
public class PushActionDTO {
    private String objectUuid;
    private Map<String, String> parameters;
}
