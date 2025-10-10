#!/usr/bin/env python3
"""
ABOUTME: Utility script to generate encryption key for securing API keys and secrets.
ABOUTME: Run this once and add the generated key to your .env file.
"""

from cryptography.fernet import Fernet

def main():
    """Generate and display a new encryption key."""
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')
    
    print("=" * 80)
    print("ENCRYPTION KEY GENERATED")
    print("=" * 80)
    print()
    print("Add this line to your .env file:")
    print()
    print(f"ENCRYPTION_KEY={key_str}")
    print()
    print("=" * 80)
    print("⚠️  IMPORTANT:")
    print("- Keep this key secure and backed up!")
    print("- Never commit this key to version control")
    print("- If you lose this key, you cannot decrypt existing data")
    print("- Use different keys for dev/staging/production")
    print("=" * 80)

if __name__ == "__main__":
    main()

