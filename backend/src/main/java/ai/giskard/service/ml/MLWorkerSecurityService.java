package ai.giskard.service.ml;

import ai.giskard.ml.tunnel.DecryptionResult;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufUtil;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class MLWorkerSecurityService {
    public static final int KEY_EXPIRY_PERIOD_SECONDS = 10;
    public static final int KEY_ID_LENGTH_BYTES = 8;

    private static final Map<String, MLWorkerSecretKey> issuedKeys = new ConcurrentHashMap<>();

    /**
     * Adds a new key to the issuedKeys dictionary.
     * Key is sent to ML Worker though a HTTP(s) client request.
     * If ML Worker doesn't try to connect using the specified key in KEY_EXPIRY_PERIOD_SECONDS, the key is
     * considered as obsolete and is deleted resulting in an ML Worker connection retry
     */
    public MLWorkerSecretKey registerVacantKey(String login) {
        cleanExpiredKeys();
        MLWorkerSecretKey key = new MLWorkerSecretKey(login);
        issuedKeys.put(key.getKeyId(), key);
        return key;
    }

    public MLWorkerSecretKey findKey(String keyId) {
        cleanExpiredKeys();
        return issuedKeys.get(keyId);
    }

    public void removeKey(String keyId) {
        issuedKeys.remove(keyId);
    }

    private void cleanExpiredKeys() {
        issuedKeys.forEach((keyId, key) -> {
            Instant expiryDate = key.getCreationDate().plus(KEY_EXPIRY_PERIOD_SECONDS, ChronoUnit.SECONDS);
            if (!key.isUsed() && Instant.now().isAfter(expiryDate)) {
                issuedKeys.remove(keyId);
            }
        });
    }

    public DecryptionResult decryptWithKeyHeader(ByteBuf in) {
        byte[] keyIdBytes = ByteBufUtil.getBytes(in.readBytes(KEY_ID_LENGTH_BYTES));
        String keyId = new String(keyIdBytes, StandardCharsets.UTF_8);
        SecretKey key = findKey(keyId).getKey();

        MLWorkerDataEncryptor encryptor = new MLWorkerDataEncryptor(key);

        ByteBuf clearData = encryptor.decryptPayload(in, keyIdBytes);
        return new DecryptionResult(keyId, clearData);
    }
}
