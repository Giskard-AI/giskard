package ai.giskard.service.ee;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.service.FileLocationService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.bouncycastle.util.encoders.Hex;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.util.Base64;

@Service
@RequiredArgsConstructor
public class LicenseService {

    private final Logger log = LoggerFactory.getLogger(LicenseService.class);

    private final FileLocationService fileLocationService;

    private final ApplicationProperties properties;

    private License currentLicense = new License();

    /**
     * On service init, load the stored license if it exists
     * Also initialize default license (for now)
     */
    @PostConstruct
    public void init() {
        try {
            this.currentLicense = readLicenseFromFile();
        } catch (LicenseException e) {
            log.warn("Invalid license file", e);
        }
    }

    public synchronized License readLicenseFromFile() {
        if (Files.exists(fileLocationService.licensePath())) {
            try {
                String licenseFile = Files.readString(fileLocationService.licensePath());
                return readLicense(licenseFile);
            } catch (IOException e) {
                log.warn("Invalid license file", e);
            }
        }
        return new License();
    }

    /**
     * Shorthand for LicenseService.getCurrentLicense().hasFeature(flag) since it's a very common call
     *
     * @param flag FeatureFlag we want to check
     * @return whether the provided flag is enabled or not
     */
    public boolean hasFeature(FeatureFlag flag) {
        return this.getCurrentLicense().hasFeature(flag);
    }

    public synchronized License getCurrentLicense() {
        return currentLicense;
    }

    /**
     * Takes a license file content, parses it, validates that it is a proper license.
     * If it's a real license, saves it in giskard home and updates available feature flags
     *
     * @param licenseContent
     */
    public synchronized void uploadLicense(String licenseContent) throws IOException {
        currentLicense = readLicense(licenseContent);
        Files.write(fileLocationService.licensePath(), licenseContent.getBytes());
    }

    private License readLicense(String lic) throws IOException {
        // 1. Remove start/end decorators
        String encodedPayload = lic.replaceAll(
            "(?:^-----BEGIN LICENSE FILE-----\\n)|" + // NOSONAR
                "\\n|" +
                "(?:-----END LICENSE FILE-----\\n$)", // NOSONAR
            "");

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
            throw new LicenseException("Incorrect algorithm, base64+ed25519 is expected");
        }

        // 4. Decode signing bytes and use signature to validate
        if (!verifySignature(encodedData, encodedSig)) {
            throw new LicenseException("Invalid signature");
        }

        // 5. Decode license and parse it into a License object
        String decodedLicense = new String(Base64.getDecoder().decode(encodedData));
        JsonNode licenseJson = mapper.readTree(decodedLicense);

        verifyExpired(licenseJson);

        License newLicense = KeygenLicenseReader.read(licenseJson);
        if (!newLicense.isActive()) {
            throw new LicenseException("License is inactive");
        }
        return newLicense;
    }


    private boolean verifySignature(String encodedData, String encodedSig) {
        byte[] publicKeyBytes = Hex.decode(properties.getLicensePublicKey());
        byte[] signatureBytes = Base64.getDecoder().decode(encodedSig);
        byte[] encDataBytes = String.format("license/%s", encodedData).getBytes();

        Ed25519PublicKeyParameters verifierParams = new Ed25519PublicKeyParameters(publicKeyBytes, 0);
        Ed25519Signer verifier = new Ed25519Signer();

        verifier.init(false, verifierParams);
        verifier.update(encDataBytes, 0, encDataBytes.length);

        return verifier.verifySignature(signatureBytes);
    }

    private void verifyExpired(JsonNode json) {
        JsonNode attributes = json.get("data").get("attributes");
        Instant now = Instant.now();
        Instant created = ZonedDateTime.parse(attributes.get("created").asText()).toInstant();
        Instant expiry = ZonedDateTime.parse(attributes.get("expiry").asText()).toInstant();
        if (now.isBefore(created)) {
            throw new LicenseException("License created date: %s is before current date, check server date".formatted(created));
        }
        if (now.isAfter(expiry)) {
            throw new LicenseException("License has expired on %s".formatted(expiry));
        }
    }
}
