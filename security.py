"""
security.py
------------
Handles password hashing and verification.

Design note:
The user asked for a "simple" local auth system. Storing raw plain-text
passwords in a JSON file is risky even on a local machine (accidental
backups, screen shares, git commits, etc). This module keeps things just
as simple to use, but stores a salted SHA-256 hash instead of the raw
password — no external auth libraries required, zero extra setup.
"""

import hashlib
import os
import secrets


def generate_salt() -> str:
    """Generate a new random salt (hex string)."""
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    """
    Hash a password with the given salt using SHA-256.
    Returns a hex digest string safe to store in JSON.
    """
    salted = f"{salt}{password}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def create_credentials(password: str) -> dict:
    """
    Create a new salt + hash pair for a brand-new user.
    Store the returned dict's values directly in users.json.
    """
    salt = generate_salt()
    hashed = hash_password(password, salt)
    return {"salt": salt, "password_hash": hashed}


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """
    Verify a login attempt against the stored salt + hash.
    Uses constant-time comparison to avoid timing attacks.
    """
    if not salt or not stored_hash:
        return False
    attempt_hash = hash_password(password, salt)
    return secrets.compare_digest(attempt_hash, stored_hash)


if __name__ == "__main__":
    # Quick manual test / utility: generate credentials for a new user
    pw = "admin123"
    creds = create_credentials(pw)
    print("Sample credentials for users.json:")
    print(creds)
    print("Verify correct password:", verify_password(pw, creds["salt"], creds["password_hash"]))
    print("Verify wrong password:", verify_password("wrong", creds["salt"], creds["password_hash"]))
