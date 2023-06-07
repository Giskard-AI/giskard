package ai.giskard.service.ml;

import ai.giskard.service.GiskardRuntimeException;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufUtil;
import io.netty.buffer.Unpooled;
import lombok.AllArgsConstructor;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import java.nio.ByteBuffer;
import java.security.SecureRandom;

@AllArgsConstructor
public class MLWorkerDataEncryptor {
    public static final int GCM_IV_LENGTH_BYTES = 16;
    public static final int AUTH_TAG_LENGTH_BYTES = 16;
    public static final String CIPHER_TRANSFORMATION = "AES/GCM/NoPadding";

    private SecretKey key;


    public byte[] encrypt(byte[] plainData) {
        return encrypt(plainData, null);
    }

    /**
     * Result message format:
     * - Cleartext payload length header, contains the sum of bytes for the rest of the fields <4 bytes>
     * - Cleartext additional_data (Optional)
     * - IV (Initialization vector) <GCM_IV_LENGTH_BYTES bytes>
     * - Encrypted data
     * - Authentication tag <AUTH_TAG_LENGTH_BYTES bytes>
     */
    public byte[] encrypt(byte[] plainPayload, byte[] associatedData) {
        byte[] encrypted = encryptPayload(plainPayload, associatedData);

        ByteBuf out = Unpooled.buffer();
        int length = (associatedData != null ? associatedData.length : 0) + encrypted.length;

        out.writeInt(length);
        if (associatedData != null) {
            out.writeBytes(associatedData);
        }
        out.writeBytes(encrypted);
        return ByteBufUtil.getBytes(out);
    }

    private byte[] encryptPayload(byte[] plainData, byte[] associatedData) {
        try {
            byte[] iv = new byte[GCM_IV_LENGTH_BYTES];
            new SecureRandom().nextBytes(iv);
            final Cipher cipher = Cipher.getInstance(CIPHER_TRANSFORMATION);
            GCMParameterSpec parameterSpec = new GCMParameterSpec(AUTH_TAG_LENGTH_BYTES * 8, iv);
            cipher.init(Cipher.ENCRYPT_MODE, key, parameterSpec);

            if (associatedData != null) {
                cipher.updateAAD(associatedData);
            }

            byte[] cipherText = cipher.doFinal(plainData);

            ByteBuffer byteBuffer = ByteBuffer.allocate(iv.length + cipherText.length);
            byteBuffer.put(iv);
            byteBuffer.put(cipherText);
            return byteBuffer.array();
        } catch (Exception e) {
            throw new GiskardRuntimeException("Failed to encrypt ML Worker data", e);
        }
    }

    public ByteBuf decryptPayload(ByteBuf in) {
        return decryptPayload(in, null);
    }

    public ByteBuf decryptPayload(ByteBuf in, byte[] associatedData) {
        byte[] iv = ByteBufUtil.getBytes(in.readBytes(MLWorkerSecretKey.KEY_SIZE_BITS / 8));
        try {
            Cipher cipher = Cipher.getInstance(CIPHER_TRANSFORMATION);
            GCMParameterSpec params = new GCMParameterSpec(GCM_IV_LENGTH_BYTES * 8, iv);
            cipher.init(Cipher.DECRYPT_MODE, key, params);
            if (associatedData != null) {
                cipher.updateAAD(associatedData);
            }
            byte[] clearData = cipher.doFinal(ByteBufUtil.getBytes(in.readBytes(in.readableBytes())));

            return Unpooled.wrappedBuffer(clearData);
        } catch (Exception e) {
            throw new GiskardRuntimeException("Failed to decrypt ML Worker data", e);
        }
    }


}
