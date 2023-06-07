package ai.giskard.service.ml;

import ai.giskard.service.GiskardRuntimeException;
import lombok.Getter;
import lombok.Setter;
import org.apache.commons.lang3.RandomStringUtils;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Base64;

@Getter
public class MLWorkerSecretKey {
    public static final int KEY_SIZE_BITS = 128;
    private String keyId = RandomStringUtils.randomAlphanumeric(8).toLowerCase(); // NOSONAR
    private final SecretKey key;
    private String login;
    private final Instant creationDate = Instant.now();
    @Setter
    private boolean used = false;

    public MLWorkerSecretKey(String login) {
        this.login = login;
        KeyGenerator keyGenerator;
        try {
            keyGenerator = KeyGenerator.getInstance("AES");
        } catch (NoSuchAlgorithmException e) {
            throw new GiskardRuntimeException("Failed to instantiate secret key", e);
        }
        keyGenerator.init(KEY_SIZE_BITS);
        this.key = keyGenerator.generateKey();
    }

    public String toBase64() {
        return Base64.getEncoder().encodeToString(key.getEncoded());
    }
}
