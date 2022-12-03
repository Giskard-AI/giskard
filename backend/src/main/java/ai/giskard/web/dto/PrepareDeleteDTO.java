package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class PrepareDeleteDTO {
    @JsonProperty("totalUsage")
    private int totalUsage() {
        return feedbackCount + suiteCount;
    }

    private int feedbackCount;
    private int suiteCount;

}
