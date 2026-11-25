import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.errors import AppError


async def hash_password(value):
    return (await asyncio.to_thread(bcrypt.hashpw, value.encode(), bcrypt.gensalt(rounds=12))).decode()


async def verify_password(value, hashed):
    try:
        return await asyncio.to_thread(bcrypt.checkpw, value.encode(), hashed.encode())
    except ValueError:
        return False


def issue_token(user, settings):
    now = datetime.now(timezone.utc)
    payload = {"sub": user["id"], "role": user["role"], "ver": user.get("token_version", 0),
               "iat": now, "exp": now + timedelta(minutes=settings.jwt_minutes), "jti": str(uuid.uuid4()),
               "iss": "busan-youth-api", "aud": "busan-youth-web"}
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")


def decode_token(value, settings):
    try:
        return jwt.decode(value, settings.jwt_secret.get_secret_value(), algorithms=["HS256"],
                          issuer="busan-youth-api", audience="busan-youth-web",
                          options={"require": ["exp", "sub", "jti", "ver"]})
    except jwt.InvalidTokenError as exc:
        raise AppError(401, "UNAUTHORIZED", "로그인이 만료되었거나 유효하지 않습니다.") from exc


def email_hash(email):
    return hashlib.sha256(email.lower().encode()).hexdigest()
