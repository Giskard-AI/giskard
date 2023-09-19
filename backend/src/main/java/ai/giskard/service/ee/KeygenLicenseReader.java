package ai.giskard.service.ee;

import com.fasterxml.jackson.databind.JsonNode;

import java.time.Instant;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;

public class KeygenLicenseReader {
    private KeygenLicenseReader() {
    }

    public static License read(JsonNode json) {
        List<String> feats = new ArrayList<>();
        JsonNode policyAttrs = null;

        if (json.has("included")) {
            for (JsonNode included : json.get("included")) {
                if ("policies".equals(included.get("type").asText())) {
                    policyAttrs = included.get("attributes"); // NOSONAR

                }
                if ("entitlements".equals(included.get("type").asText())) {
                    feats.add(included.get("attributes").get("code").asText()); // NOSONAR
                }
            }
        }
        if (policyAttrs == null) {
            throw new LicenseException("Couldn't find policy details in license");
        }


        JsonNode policyMeta = policyAttrs.get("metadata");

        License license = new License();
        license.setPlanName(policyMeta.get("planName").asText());
        license.setPlanCode(policyMeta.get("planCode").asText());

        if (policyMeta.has("projectLimit")) {
            license.setProjectLimit(policyMeta.get("projectLimit").asInt(0));
        }

        if (policyMeta.has("userLimit")) {
            license.setUserLimit(policyMeta.get("userLimit").asInt(0));
        }

        if (policyMeta.has("modelPerProjectLimit")) {
            license.setModelPerProjectLimit(policyMeta.get("modelPerProjectLimit").asInt(0));
        }

        license.setFeatures(feats);
        JsonNode licenseAttributes = json.get("data").get("attributes"); // NOSONAR

        Instant expiry = ZonedDateTime.parse(licenseAttributes.get("expiry").asText()).toInstant();
        license.setActive("ACTIVE".equals(licenseAttributes.get("status").asText()) && expiry.isAfter(Instant.now()));
        license.setExpiresOn(expiry);

        license.setId(json.get("data").get("id").asText());
        return license;
    }
}
