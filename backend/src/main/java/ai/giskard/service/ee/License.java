package ai.giskard.service.ee;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Getter
@Setter
public class License {
    private boolean active;
    private String planName;
    private String planCode;
    private List<String> features;

    public Map<FeatureFlagService.FeatureFlag, Boolean> getFeatures() {
        Map<FeatureFlagService.FeatureFlag, Boolean> map = new HashMap<>();

        for (FeatureFlagService.FeatureFlag featureFlag : FeatureFlagService.FeatureFlag.values()) {
            map.put(featureFlag, false);
        }

        if (features != null) {
            for (String feat : features) {
                map.put(FeatureFlagService.FeatureFlag.valueOf(feat), true);
            }
        }

        return map;
    }

    public boolean hasFeature(FeatureFlagService.FeatureFlag flag) {
        return this.getFeatures().get(flag);
    }

    public static License fromJson(JsonNode licenseJson) {
        JsonNode attributes = licenseJson.get("data").get("attributes");
        JsonNode included = licenseJson.get("included");

        License newLicense = new License();
        newLicense.setPlanName(attributes.get("metadata").get("planName").asText());
        newLicense.setPlanCode(attributes.get("metadata").get("planCode").asText());

        List<String> feats = new ArrayList<>();
        for (JsonNode include : included) {
            if (!"entitlements".equals(include.get("type").asText())) {
                continue;
            }

            feats.add(include.get("attributes").get("code").asText());
        }

        newLicense.setFeatures(feats);
        newLicense.setActive("ACTIVE".equals(attributes.get("status").asText()));
        return newLicense;
    }
}
