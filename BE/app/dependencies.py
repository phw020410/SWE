from typing import Annotated
import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import AppError
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def context(request: Request):
    return request.app.state


async def current_user(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        raise AppError(401, "UNAUTHORIZED", "로그인이 필요합니다.")
    state = request.app.state
    claims = decode_token(credentials.credentials, state.settings)
    try:
        uuid.UUID(claims["sub"])
        uuid.UUID(claims["jti"])
    except (ValueError, TypeError):
        raise AppError(401, "UNAUTHORIZED", "유효하지 않은 토큰입니다.")
    user = await state.repository.get_user(claims["sub"])
    if not user or user.get("token_version", 0) != claims["ver"] or await state.repository.is_revoked(claims["jti"]):
        raise AppError(401, "UNAUTHORIZED", "로그인이 만료되었거나 유효하지 않습니다.")
    request.state.user_id = user["id"]
    request.state.claims = claims
    return user


async def admin(user=Depends(current_user)):
    if user["role"] != "ADMIN":
        raise AppError(403, "FORBIDDEN", "관리자 권한이 필요합니다.")
    return user
