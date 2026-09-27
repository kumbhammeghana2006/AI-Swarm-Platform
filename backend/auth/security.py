import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt

from backend.config import settings

def hash_password(password: str) -> str:
    """
    Hashes a plain password using modern scrypt algorithm with CSPRNG salt.
    Format returned: scrypt$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(16)
    hash_bytes = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1
    )
    return f"scrypt${salt.hex()}${hash_bytes.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against stored scrypt hash using constant-time comparison.
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3 or parts[0] != "scrypt":
            return False
        salt = bytes.fromhex(parts[1])
        expected_hash = bytes.fromhex(parts[2])
        
        computed_hash = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1
        )
        return secrets.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and verifies a JWT token. Returns payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
