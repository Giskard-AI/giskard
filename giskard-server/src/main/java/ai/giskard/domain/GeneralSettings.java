package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class GeneralSettings {
    @JsonProperty(value = "isAnalyticsEnabled")
    private boolean isAnalyticsEnabled = true;

}
