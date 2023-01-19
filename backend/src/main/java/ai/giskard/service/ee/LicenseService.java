package ai.giskard.service.ee;

import ai.giskard.service.GiskardRuntimeException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.bouncycastle.util.encoders.Hex;
import org.springframework.stereotype.Service;

import java.util.Base64;

@Service
public class LicenseService {

    private static final String SIGNATURE_KEY = "c947f66224d465b50004c327fc831cff672fc07b540b0613d6f661d0e72d455d";

    private class License {
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
        

        return null;
    }
}
