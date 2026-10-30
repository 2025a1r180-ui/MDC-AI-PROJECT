"""
Security module for Echo Journal.
Provides scrypt-based password hashing, constant-time verification,
cryptographic CSRF token generation/validation, and HMAC session signing.
"""

import os
import hmac
import hashlib
import secrets
import html
import base64
import json
import time
from typing import Tuple, Optional


def hash_password(password: str) -> str:
    """
    Hash a password using scrypt (memory-hard key derivation function).
    Format: scrypt$n$r$p$salt_hex$hash_hex
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    
    salt = os.urandom(16)
    # Standard scrypt parameters recommended by OWASP
    n, r, p = 16384, 8, 1
    key_len = 64
    
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        maxmem=0x2000000,
        dklen=key_len
    )
    
    salt_hex = salt.hex()
    hash_hex = derived.hex()
    return f"scrypt${n}${r}${p}${salt_hex}${hash_hex}"


def verify_password(password: str, hashed_value: str) -> bool:
    """
    Verify a plain password against the stored scrypt hash using constant-time comparison.
    """
    if not password or not hashed_value:
        return False
        
    try:
        parts = hashed_value.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            return False
            
        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt = bytes.fromhex(parts[4])
        expected_hash = bytes.fromhex(parts[5])
        
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=0x2000000,
            dklen=len(expected_hash)
        )
        return hmac.compare_digest(derived, expected_hash)
    except Exception:
        return False


def generate_csrf_token() -> str:
    """Generate a high-entropy cryptographically secure CSRF token."""
    return secrets.token_hex(32)


def verify_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token using constant-time string comparison."""
    if not token or not session_token:
        return False
    return hmac.compare_digest(token, session_token)


def sanitize_text(text: str) -> str:
    """Sanitize and HTML-escape text to prevent XSS attacks while preserving unicode."""
    if text is None:
        return ""
    return html.escape(text.strip(), quote=True)


def sign_session_data(data: dict, secret_key: str) -> str:
    """
    Create a cryptographically signed session string: payload.signature
    using HMAC-SHA256 with timestamp.
    """
    payload_dict = {
        "data": data,
        "ts": int(time.time())
    }
    raw_payload = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_payload).decode("utf-8").rstrip("=")
    
    mac = hmac.new(
        secret_key.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return f"{b64_payload}.{mac}"


def verify_session_data(signed_str: str, secret_key: str, max_age_seconds: int = 86400 * 7) -> Optional[dict]:
    """
    Verify and unpack a signed session string. Returns None if invalid or expired.
    """
    if not signed_str or "." not in signed_str:
        return None
        
    try:
        b64_payload, signature = signed_str.split(".", 1)
        expected_mac = hmac.new(
            secret_key.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_mac):
            return None
            
        # Re-add padding for base64 decoding
        padding = "=" * (4 - (len(b64_payload) % 4)) if len(b64_payload) % 4 != 0 else ""
        raw_payload = base64.urlsafe_b64decode(b64_payload + padding)
        payload_dict = json.loads(raw_payload.decode("utf-8"))
        
        # Check expiry
        issued_at = payload_dict.get("ts", 0)
        if time.time() - issued_at > max_age_seconds:
            return None
            
        return payload_dict.get("data")
    except Exception:
        return None
