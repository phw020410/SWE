import uuid

from app.errors import AppError
from app.repositories.base import now_iso
from app.security import hash_password, issue_token, verify_password


class AuthService:
    def __init__(self, settings, repository):
        self.settings, self.repository = settings, repository

    async def register(self, body):
        email = str(body.email).lower()
        if await self.repository.find_user(email):
            raise AppError(409, "DUPLICATE_EMAIL", "이미 가입된 이메일입니다.")
        stamp = now_iso()
        return await self.repository.create_user({"id": str(uuid.uuid4()), "email": email,
            "password_hash": await hash_password(body.password), "name": body.name, "role": "USER",
            "token_version": 0, "created_at": stamp, "updated_at": stamp})

    async def authenticate(self, email, password):
        user = await self.repository.find_user(str(email).lower())
        if not user or not await verify_password(password, user["password_hash"]):
            raise AppError(401, "LOGIN_FAILED", "이메일 또는 비밀번호가 올바르지 않습니다.")
        return user, issue_token(user, self.settings)

    async def update_profile(self, user, body):
        if not await verify_password(body.current_password, user["password_hash"]):
            raise AppError(400, "INVALID_INPUT", "현재 비밀번호가 올바르지 않습니다.")
        changes = {"updated_at": now_iso()}
        if body.name is not None:
            changes["name"] = body.name
        if body.new_password:
            changes["password_hash"] = await hash_password(body.new_password)
            changes["token_version"] = user.get("token_version", 0) + 1
        return await self.repository.update_user(user["id"], changes)
