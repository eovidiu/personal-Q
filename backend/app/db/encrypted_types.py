"""
ABOUTME: Custom SQLAlchemy types for encrypted data storage.
ABOUTME: Automatically encrypts on write and decrypts on read transparently.
"""

import logging
from sqlalchemy import LargeBinary, TypeDecorator

logger = logging.getLogger(__name__)


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type that encrypts strings before storing in database.
    
    Data is stored as binary (encrypted bytes) in the database,
    but appears as regular strings in Python code.
    """
    
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """
        Encrypt value when saving to database.

        Args:
            value: Plaintext string to encrypt
            dialect: Database dialect (unused)

        Returns:
            Encrypted bytes or None
        """
        if value is not None:
            try:
                # Import here to avoid circular dependency
                from app.services.encryption_service import encryption_service
                return encryption_service.encrypt(value)
            except Exception as e:
                logger.error(f"Failed to encrypt value: {e}")
                raise

        return value

    def process_result_value(self, value, dialect):
        """
        Decrypt value when reading from database.

        Args:
            value: Encrypted bytes from database
            dialect: Database dialect (unused)

        Returns:
            Decrypted plaintext string or None
        """
        if value is not None:
            try:
                # Import here to avoid circular dependency
                from app.services.encryption_service import encryption_service
                return encryption_service.decrypt(value)
            except Exception as e:
                logger.error(f"Failed to decrypt value: {e}")
                raise

        return value

