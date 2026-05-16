"""
JWT auth using Python stdlib only (hmac + hashlib) — no cryptography dependency.
Implements HS256 (HMAC-SHA256) as per RFC 7519.
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ACCESS_TOKEN_EXPIRE_SECONDS = 24 * 3600


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def _sign(msg: str, secret: str) -> str:
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
    return _b64url_encode(sig)


def create_access_token(data: dict, expires_in: int = ACCESS_TOKEN_EXPIRE_SECONDS) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = {**data, "exp": int(time.time()) + expires_in, "iat": int(time.time())}
    body = _b64url_encode(json.dumps(payload).encode())
    sig = _sign(f"{header}.{body}", settings.SECRET_KEY)
    return f"{header}.{body}.{sig}"


def decode_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        expected = _sign(f"{header}.{body}", settings.SECRET_KEY)
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64url_decode(body))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    if not token:
        return None
    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        return None
    return {"username": payload["sub"], "is_admin": payload.get("is_admin", False)}


async def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès admin requis")
    return user
