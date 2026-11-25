import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response

from app.dependencies import current_user
from app.errors import AppError
from app.observability import request_id
from app.schemas import Login, Profile, Signup
from app.security import email_hash
from app.services.auth import AuthService

router = APIRouter(tags=["인증·사용자"])
log = logging.getLogger("platform")


def public_user(user):
    return {"userId": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}


@router.post("/api/auth/signup", status_code=201)
async def signup(body: Signup, request: Request):
    state = request.app.state
    user = await AuthService(state.settings, state.repository).register(body)
    return public_user(user)


@router.post("/api/auth/login")
async def login(body: Login, request: Request, response: Response):
    state = request.app.state
    try:
        user, token = await AuthService(state.settings, state.repository).authenticate(body.email, body.password)
    except AppError:
        log.warning(json.dumps({"event": "login_failed", "requestId": request_id.get(), "emailHash": email_hash(str(body.email)), "ip": request.client.host if request.client else None}))
        raise
    response.headers["Cache-Control"] = "no-store"
    return {"accessToken": token, "tokenType": "bearer", "expiresIn": state.settings.jwt_minutes * 60, "user": public_user(user)}


@router.post("/api/auth/logout", status_code=204)
async def logout(request: Request, user=Depends(current_user)):
    claims = request.state.claims
    await request.app.state.repository.revoke(claims["jti"], datetime.fromtimestamp(claims["exp"], timezone.utc).isoformat())
    return Response(status_code=204)


@router.get("/api/users/me")
async def me(user=Depends(current_user)):
    return public_user(user)


@router.patch("/api/users/me")
async def update(body: Profile, request: Request, user=Depends(current_user)):
    state = request.app.state
    return public_user(await AuthService(state.settings, state.repository).update_profile(user, body))
