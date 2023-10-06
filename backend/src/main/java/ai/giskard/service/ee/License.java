package ai.giskard.service.ee;

import lombok.Getter;
import lombok.Setter;

import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Getter
@Setter
public class License {
    private String id;
    private boolean active;
    private String planName;
    private String planCode;
    private List<String> features;

    private Integer projectLimit;
    private Integer modelPerProjectLimit;
    private Integer userLimit;
    private Instant expiresOn;

    public Map<FeatureFlag, Boolean> getFeatures() {
        Map<FeatureFlag, Boolean> map = new HashMap<>();

        for (FeatureFlag featureFlag : FeatureFlag.values()) {
            map.put(featureFlag, false);
        }

        if (features != null) {
            for (String feat : features) {
                map.put(FeatureFlag.valueOf(feat), true);
            }
        }

        return map;
    }

    public boolean hasFeature(FeatureFlag flag) {
        return this.getFeatures().get(flag);
    }

}
