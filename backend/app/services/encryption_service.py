"""
ABOUTME: Encryption service for securing sensitive data at rest using Fernet symmetric encryption.
ABOUTME: All API keys and secrets are encrypted before storage in database.
"""

import logging
import os
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self):
        """Initialize encryption service with key from environment."""
        self._cipher = None
        self._key = None
        self._initialize()

    def _initialize(self):
        """Initialize the cipher with encryption key."""
        # Get encryption key from environment
        key_str = os.getenv("ENCRYPTION_KEY")

        if not key_str:
            logger.warning(
                "ENCRYPTION_KEY not set in environment. "
                "Generating a new key for this session. "
                "This key will be lost on restart!"
            )
            # Generate a new key for this session
            # In production, this should be set in environment and persisted
            key_str = Fernet.generate_key().decode()
            logger.warning(f"Generated encryption key: {key_str}")
            logger.warning("Add this to your .env file: ENCRYPTION_KEY={key_str}")

        try:
            self._key = key_str.encode() if isinstance(key_str, str) else key_str
            self._cipher = Fernet(self._key)
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise ValueError(f"Invalid encryption key: {e}")

    @property
    def cipher(self) -> Fernet:
        """Get Fernet cipher instance."""
        if self._cipher is None:
            self._initialize()
        return self._cipher

    def encrypt(self, plaintext: Optional[str]) -> Optional[bytes]:
        """
        Encrypt plaintext string to bytes.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted bytes, or None if input is None
        """
        if plaintext is None or plaintext == "":
            return None

        try:
            encrypted = self.cipher.encrypt(plaintext.encode("utf-8"))
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: Optional[bytes]) -> Optional[str]:
        """
        Decrypt bytes to plaintext string.

        Args:
            ciphertext: Bytes to decrypt

        Returns:
            Decrypted string, or None if input is None
        """
        if ciphertext is None:
            return None

        try:
            decrypted = self.cipher.decrypt(ciphertext)
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.

        Returns:
            Base64-encoded encryption key as string
        """
        key = Fernet.generate_key()
        return key.decode("utf-8")


# Global encryption service instance
encryption_service = EncryptionService()


def get_encryption_service() -> EncryptionService:
    """Get encryption service instance."""
    return encryption_service
