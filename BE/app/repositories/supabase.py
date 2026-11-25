import httpx

from app.errors import AppError, DatabaseError
from app.repositories.base import now_iso


class SupabaseRepository:
    """서버 전용 service-role + PostgREST. save_chat_turn RPC가 턴 전체를 원자적으로 저장한다."""
    def __init__(self, settings, client):
        self.client = client
        self.url = settings.supabase_url.rstrip("/") + "/rest/v1"
        key = settings.supabase_service_role_key.get_secret_value()
        self.headers = {"apikey": key, "Authorization": "Bearer " + key, "Prefer": "return=representation"}

    async def _call(self, method, path, params=None, body=None):
        try:
            r = await self.client.request(method, self.url + path, params=params, json=body, headers=self.headers, timeout=2)
            if r.status_code == 409:
                raise AppError(409, "DUPLICATE_EMAIL", "이미 가입된 이메일입니다.")
            if r.status_code >= 400:
                try:
                    code = r.json().get("code")
                except ValueError:
                    code = None
                if code == "P0002":
                    raise AppError(404, "NOT_FOUND", "대화를 찾을 수 없습니다.")
                if code == "57014":
                    raise AppError(504, "TIMEOUT", "처리시간을 초과했습니다. 다시 시도해 주세요.")
                raise DatabaseError()
            return r.json() if r.content else None
        except (httpx.HTTPError, ValueError) as exc:
            raise DatabaseError() from exc

    async def initialize(self):
        # 원격 스키마 변경은 migration 파일을 명시적으로 적용한다.
        return None

    async def ping(self):
        await self._call("GET", "/users", {"select": "id", "limit": "0"})

    async def find_user(self, email):
        rows = await self._call("GET", "/users", {"email": "eq." + email, "select": "*", "limit": "1"})
        return rows[0] if rows else None

    async def get_user(self, user_id):
        rows = await self._call("GET", "/users", {"id": "eq." + user_id, "select": "*", "limit": "1"})
        return rows[0] if rows else None

    async def create_user(self, record):
        return (await self._call("POST", "/users", body=record))[0]

    async def update_user(self, user_id, changes):
        return (await self._call("PATCH", "/users", {"id": "eq." + user_id}, changes))[0]

    async def revoke(self, jti, expires_at):
        # JTI가 이미 취소돼 있어도 로그아웃은 성공으로 취급한다.
        await self._call("POST", "/rpc/revoke_access_token", body={"p_jti": jti, "p_expires_at": expires_at})

    async def is_revoked(self, jti):
        return bool(await self._call("GET", "/revoked_tokens", {"jti": "eq." + jti, "expires_at": "gt." + now_iso(), "select": "jti"}))

    async def conversation(self, user_id, conversation_id):
        rows = await self._call("GET", "/conversations", {"user_id": "eq." + user_id, "id": "eq." + conversation_id, "select": "*"})
        if not rows:
            raise AppError(404, "NOT_FOUND", "대화를 찾을 수 없습니다.")
        return rows[0]

    async def history(self, user_id, limit=30, offset=0):
        return await self._call("POST", "/rpc/get_chat_history", body={"p_user_id": user_id, "p_limit": limit, "p_offset": offset})

    async def full_conversation(self, user_id, conversation_id):
        rows = await self._call("POST", "/rpc/get_chat_history", body={"p_user_id": user_id, "p_limit": 1, "p_offset": 0, "p_conversation_id": conversation_id})
        if not rows:
            raise AppError(404, "NOT_FOUND", "대화를 찾을 수 없습니다.")
        return rows[0]

    async def save_turn(self, payload):
        return await self._call("POST", "/rpc/save_chat_turn", body={"p": payload})

    async def get_cache(self, cache_key):
        rows = await self._call("GET", "/api_cache", {"cache_key": "eq." + cache_key, "expires_at": "gt." + now_iso(), "select": "response", "limit": "1"})
        return rows[0]["response"] if rows else None

    async def stats(self):
        return await self._call("POST", "/rpc/admin_stats", body={})

    async def clear_cache(self):
        await self._call("DELETE", "/api_cache", {"cache_key": "not.is.null"})
