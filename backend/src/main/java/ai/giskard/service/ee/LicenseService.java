package ai.giskard.service.ee;

import ai.giskard.service.GiskardRuntimeException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.Setter;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.bouncycastle.util.encoders.Hex;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class LicenseService {

    private static final String SIGNATURE_KEY = "c947f66224d465b50004c327fc831cff672fc07b540b0613d6f661d0e72d455d";

    @Getter
    @Setter
    public class License {
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
    }

    private License license;

    public License getCurrentLicense() {
        License defaultLicense = new License();
        defaultLicense.setPlanName("Open Source");
        return license == null ? defaultLicense : license;
    }

    /**
     * Checks if there currently is a license. If yes, parses and loads it.
     */
    public void loadLicense() {

    }

    /**
     * Takes a license file content, parses it, validates that it is a proper license.
     * If it's a real license, saves it in giskard home and updates available feature flags
     *
     * @param licenseFile
     */
    public void uploadLicense(String licenseFile) throws JsonProcessingException {
        decodeLicense(licenseFile);
    }

    private License decodeLicense(String lic) throws JsonProcessingException {
        // 1. Remove start/end decorators
        String encodedPayload = lic.replaceAll("(^-----BEGIN LICENSE FILE-----\\n|\\n|-----END LICENSE FILE-----\\n$)", "");

        // 2. Decode base64 => json
        byte[] payloadBytes = Base64.getDecoder().decode(encodedPayload);
        String payload = new String(payloadBytes);
        ObjectMapper mapper = new ObjectMapper();
        JsonNode payloadJson = mapper.readTree(payload);

        // 3. Parse Json
        String encodedData = payloadJson.get("enc").asText();
        String encodedSig = payloadJson.get("sig").asText();
        String algorithm = payloadJson.get("alg").asText();

        if (!"base64+ed25519".equals(algorithm)) {
            throw new GiskardRuntimeException("License file is invalid.");
        }

        // 4. Decode signing bytes and use signature to validate
        byte[] publicKeyBytes = Hex.decode(SIGNATURE_KEY);
        byte[] signatureBytes = Base64.getDecoder().decode(encodedSig);
        byte[] encDataBytes = String.format("license/%s", encodedData).getBytes();

        Ed25519PublicKeyParameters verifierParams = new Ed25519PublicKeyParameters(publicKeyBytes, 0);
        Ed25519Signer verifier = new Ed25519Signer();

        verifier.init(false, verifierParams);
        verifier.update(encDataBytes, 0, encDataBytes.length);

        if (!verifier.verifySignature(signatureBytes)) {
            throw new GiskardRuntimeException("License file is invalid.");
        }

        // 5. Decode license and parse it into a License object
        String decodedLicense = new String(Base64.getDecoder().decode(encodedData));
        JsonNode licenseJson = mapper.readTree(decodedLicense);

        JsonNode attributes = licenseJson.get("data").get("attributes");
        JsonNode included = licenseJson.get("included");
        if (!"ACTIVE".equals(attributes.get("status").asText())) {
            throw new GiskardRuntimeException("License file is invalid.");
        }

        // TODO: Check expiration

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

        this.license = newLicense;
        return newLicense;
    }
}
