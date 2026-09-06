"""
Security utilities for the recommendation platform.
"""
import hashlib
import secrets
import hmac
from typing import Optional
from ..core.config import settings

def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a salt.
    In production, use a proper password hashing library like bcrypt or Argon2.
    """
    salt = settings.password_salt or secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a stored hash.
    """
    try:
        salt, stored_hash = hashed.split('$')
        computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return hmac.compare_digest(stored_hash, computed_hash)
    except ValueError:
        return False

def generate_api_key() -> str:
    """
    Generate a random API key.
    """
    return secrets.token_urlsafe(32)

def verify_api_key(key: str) -> bool:
    """
    Verify an API key against the stored key (if using single key auth).
    """
    expected_key = settings.api_key
    if not expected_key:
        return True  # No API key required
    return hmac.compare_digest(key, expected_key)

def generate_jwt_token(user_id: str, expires_in: int = 3600) -> str:
    """
    Generate a simple JWT token (placeholder).
    In production, use a proper library like PyJWT.
    """
    # This is a simplified placeholder; do not use in production
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "exp": expires_in}
    # In real implementation, you would base64 encode and sign
    return f"{header}.{payload}.{secrets.token_hex(16)}"