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

    private Integer projectLimit;
    private Integer userLimit;

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

    public static License fromJson(JsonNode licenseJson) {
        JsonNode attributes = licenseJson.get("data").get("attributes");
        JsonNode metadata = attributes.get("metadata");

        License newLicense = new License();
        newLicense.setPlanName(metadata.get("planName").asText());
        newLicense.setPlanCode(metadata.get("planCode").asText());

        if (metadata.has("projectLimit")) {
            newLicense.setProjectLimit(metadata.get("projectLimit").asInt(0));
        }

        if (metadata.has("userLimit")) {
            newLicense.setUserLimit(metadata.get("userLimit").asInt(0));
        }

        List<String> feats = new ArrayList<>();

        if (licenseJson.has("included")) {
            JsonNode included = licenseJson.get("included");
            for (JsonNode include : included) {
                if (!"entitlements".equals(include.get("type").asText())) {
                    continue;
                }

                feats.add(include.get("attributes").get("code").asText());
            }
        }

        newLicense.setFeatures(feats);
        newLicense.setActive("ACTIVE".equals(attributes.get("status").asText()));

        return newLicense;
    }
}
