package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class PrepareDeleteDTO {

    public static class LightFeedback {
        public long id;
        public long projectId;
        public String message;
    }

    public static class LightTestSuite {
        public long id;
        public long projectId;
        public String name;
    }


    @JsonProperty("totalUsage")
    private int totalUsage() {
        int res = 0;
        if (feedbacks != null) {
            res += feedbacks.size();
        }
        if (suites != null) {
            res += suites.size();
        }
        return res;
    }

    private List<LightFeedback> feedbacks;
    private List<LightTestSuite> suites;
}
