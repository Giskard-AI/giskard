package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.apache.commons.lang3.RandomStringUtils;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class GeneralSettings {
    @JsonProperty(value = "isAnalyticsEnabled")
    private boolean isAnalyticsEnabled = true;
    private String instanceId = RandomStringUtils.randomAlphanumeric(16).toLowerCase();

    @Override
    public String toString() {
        return "GeneralSettings{" +
            "isAnalyticsEnabled=" + isAnalyticsEnabled +
            ", instanceId='" + instanceId + '\'' +
            '}';
    }
}
