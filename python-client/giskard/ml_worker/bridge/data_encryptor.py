from typing import Optional

from Crypto.Cipher import AES

KEY_LENGTH_BYTES = 16


class DataEncryptor:
    key: bytes

    def __init__(self, key: bytes) -> None:
        self.key = key

    def encrypt(self, plain_data: bytes, additional_data: Optional[bytes] = None):
        """
        Uses AES GCM authenticated encryption to create an encrypted message with headers

        Message format:
            - Cleartext payload length header, contains the sum of bytes for the rest of the fields <4 bytes>
            - Cleartext additional_data (Optional)
            - IV (Initialization vector) <16 bytes>
            - Encrypted data
            - Authentication tag <16 bytes>
        """
        cipher = AES.new(self.key, AES.MODE_GCM)
        if additional_data:
            cipher.update(additional_data)
        encrypted_data, tag = cipher.encrypt_and_digest(plain_data)

        message = cipher.nonce + encrypted_data + tag
        if additional_data:
            message = additional_data + message
        return int.to_bytes(len(message), 4, "big", signed=False) + message

    def decrypt(self, encrypted_data):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=encrypted_data[:KEY_LENGTH_BYTES])
        plain_data = cipher.decrypt_and_verify(
            encrypted_data[KEY_LENGTH_BYTES:-KEY_LENGTH_BYTES], encrypted_data[-KEY_LENGTH_BYTES:]
        )

        return plain_data
