from datetime import datetime
from datetime import timezone

from cryptography.fernet import Fernet, MultiFernet


def datetime_utc_now():
    return datetime.now(timezone.utc)


class CredentialManager:
    """Manages encryption/decryption of credentials with key rotation support"""

    def __init__(self, current_key: bytes, old_keys: list[bytes] = None):
        # Initialize with current and old keys for rotation
        keys = [Fernet(current_key)]
        if old_keys:
            keys.extend([Fernet(key) for key in old_keys])
        self.fernet = MultiFernet(keys)
        self.current_fernet = Fernet(current_key)

    def encrypt_config(self, config: dict) -> dict:
        """Encrypts sensitive fields using the current key"""
        encrypted_config = config.copy()
        sensitive_fields = ["password", "username"]

        for field in sensitive_fields:
            if field in encrypted_config:
                encrypted_config[field] = self.current_fernet.encrypt(encrypted_config[field].encode()).decode()

        return encrypted_config

    def decrypt_config(self, config: dict) -> dict:
        """Decrypts sensitive fields using current or old keys"""
        decrypted_config = config.copy()
        sensitive_fields = ["password", "username"]

        for field in sensitive_fields:
            if field in decrypted_config:
                decrypted_config[field] = self.fernet.decrypt(decrypted_config[field].encode()).decode()

        return decrypted_config
