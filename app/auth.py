from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid

def password_hash(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    value = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()
    return value, salt.hex()

def password_matches(password: str, stored: str, salt_hex: str) -> bool:
    value, _ = password_hash(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(value, stored)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def new_session(db, teacher_id: str) -> str:
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    db.execute('insert into sessions values(?,?,?,?,datetime("now"))', (str(uuid.uuid4()), teacher_id, token_hash(token), now + 30 * 86400, now))
    return token
