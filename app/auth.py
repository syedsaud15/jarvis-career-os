from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return base64.b64encode(salt + digest).decode()


def verify_password(password: str, stored: str) -> bool:
    raw = base64.b64decode(stored.encode())
    return hmac.compare_digest(raw[16:], hashlib.pbkdf2_hmac("sha256", password.encode(), raw[:16], 310000))


def create_token(email: str, secret: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"sub": email, "exp": int(time.time()) + 86400}).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_token(token: str, secret: str) -> str | None:
    try:
        payload, signature = token.split(".", 1)
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = payload + "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if int(claims.get("exp", 0)) < int(time.time()):
            return None
        return str(claims["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
