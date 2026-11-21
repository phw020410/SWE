import json
import uuid
from pathlib import Path

import aiosqlite

from app.errors import AppError, DatabaseError
from app.repositories.base import now_iso

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'USER',token_version INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,title TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,role TEXT NOT NULL,message_type TEXT NOT NULL,content TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS recommended_items(id TEXT PRIMARY KEY,message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,item_type TEXT NOT NULL,source TEXT NOT NULL,external_id TEXT NOT NULL,title TEXT NOT NULL,organization TEXT,url TEXT,raw_data TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS image_analyses(id TEXT PRIMARY KEY,message_id TEXT UNIQUE NOT NULL REFERENCES messages(id) ON DELETE CASCADE,image_type TEXT NOT NULL,extracted_data TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS api_cache(cache_key TEXT PRIMARY KEY,source TEXT NOT NULL,response TEXT NOT NULL,expires_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS revoked_tokens(jti TEXT PRIMARY KEY,expires_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS conv_user_time ON conversations(user_id,updated_at);
CREATE INDEX IF NOT EXISTS msg_conv_time ON messages(conversation_id,created_at);
"""


class SQLiteRepository:
    def __init__(self, path):
        self.path = str(Path(path).resolve())

    async def _connect(self):
        db = await aiosqlite.connect(self.path, timeout=2)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON")
        return db

    async def initialize(self):
        db = await self._connect()
        try:
            await db.executescript(SCHEMA)
            await db.commit()
        finally:
            await db.close()

    async def _query(self, sql, args=(), write=False):
        db = await self._connect()
        try:
            cursor = await db.execute(sql, args)
            rows = [dict(row) for row in await cursor.fetchall()]
            if write:
                await db.commit()
            return rows
        except aiosqlite.IntegrityError as exc:
            raise AppError(409, "DUPLICATE_EMAIL", "이미 가입된 이메일입니다.") from exc
        except aiosqlite.Error as exc:
            raise DatabaseError() from exc
        finally:
            await db.close()

    async def ping(self):
        await self._query("SELECT 1")

    async def find_user(self, email):
        rows = await self._query("SELECT * FROM users WHERE email=?", (email,))
        return rows[0] if rows else None

    async def get_user(self, user_id):
        rows = await self._query("SELECT * FROM users WHERE id=?", (user_id,))
        return rows[0] if rows else None

    async def create_user(self, record):
        await self._query("INSERT INTO users(id,email,password_hash,name,role,token_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                          tuple(record[k] for k in ["id", "email", "password_hash", "name", "role", "token_version", "created_at", "updated_at"]), True)
        return record

    async def update_user(self, user_id, changes):
        allowed = {"name", "password_hash", "token_version", "updated_at", "role"}
        values = {k: v for k, v in changes.items() if k in allowed}
        await self._query("UPDATE users SET " + ",".join(f"{k}=?" for k in values) + " WHERE id=?", (*values.values(), user_id), True)
        return await self.get_user(user_id)

    async def revoke(self, jti, expires_at):
        await self._query("INSERT OR REPLACE INTO revoked_tokens VALUES(?,?)", (jti, expires_at), True)

    async def is_revoked(self, jti):
        return bool(await self._query("SELECT jti FROM revoked_tokens WHERE jti=? AND expires_at>?", (jti, now_iso())))

    async def conversation(self, user_id, conversation_id):
        rows = await self._query("SELECT * FROM conversations WHERE user_id=? AND id=?", (user_id, conversation_id))
        if not rows:
            raise AppError(404, "NOT_FOUND", "대화를 찾을 수 없습니다.")
        return rows[0]

    async def history(self, user_id, limit=30, offset=0):
        conversations = await self._query("SELECT * FROM conversations WHERE user_id=? ORDER BY updated_at DESC LIMIT ? OFFSET ?", (user_id, limit, offset))
        return await self._hydrate(conversations)

    async def full_conversation(self, user_id, conversation_id):
        return (await self._hydrate([await self.conversation(user_id, conversation_id)]))[0]

    async def _hydrate(self, conversations):
        for conv in conversations:
            conv["messages"] = await self._query("SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at,id", (conv["id"],))
            for message in conv["messages"]:
                message["recommended_items"] = await self._query("SELECT * FROM recommended_items WHERE message_id=? ORDER BY created_at,id", (message["id"],))
                for item in message["recommended_items"]:
                    item["raw_data"] = json.loads(item["raw_data"] or "{}")
                analysis = await self._query("SELECT image_type,extracted_data FROM image_analyses WHERE message_id=?", (message["id"],))
                message["image_analysis"] = ({**analysis[0], "extracted_data": json.loads(analysis[0]["extracted_data"])} if analysis else None)
        return conversations

    async def save_turn(self, payload):
        db = await self._connect()
        try:
            await db.execute("BEGIN IMMEDIATE")
            stamp = now_iso()
            conv_id = payload.get("conversation_id") or str(uuid.uuid4())
            if payload.get("conversation_id"):
                cursor = await db.execute("SELECT id FROM conversations WHERE id=? AND user_id=?", (conv_id, payload["user_id"]))
                if not await cursor.fetchone():
                    raise AppError(404, "NOT_FOUND", "대화를 찾을 수 없습니다.")
                await db.execute("UPDATE conversations SET updated_at=? WHERE id=?", (stamp, conv_id))
            else:
                await db.execute("INSERT INTO conversations VALUES(?,?,?,?,?)", (conv_id, payload["user_id"], payload["query"][:30], stamp, stamp))
            user_message = str(uuid.uuid4())
            answer_message = str(uuid.uuid4())
            await db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?)", (user_message, conv_id, "USER", payload["message_type"], payload["query"], stamp))
            # 같은 시각에도 질문→답변 순서가 안정되도록 응답 시각을 조금 뒤로 둔다.
            from datetime import datetime, timedelta
            answer_stamp = (datetime.fromisoformat(stamp) + timedelta(microseconds=1)).isoformat()
            await db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?)", (answer_message, conv_id, "ASSISTANT", "TEXT", payload["answer"], answer_stamp))
            for item in payload.get("items", []):
                await db.execute("INSERT INTO recommended_items VALUES(?,?,?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), answer_message,
                    item["item_type"], item["source"], item["external_id"], item["title"], item.get("organization"), item.get("url"), json.dumps(item, ensure_ascii=False), stamp))
            if payload.get("image_analysis"):
                analysis = payload["image_analysis"]
                await db.execute("INSERT INTO image_analyses VALUES(?,?,?,?,?)", (str(uuid.uuid4()), user_message, analysis["image_type"], json.dumps(analysis, ensure_ascii=False), stamp))
            for entry in payload.get("cache_updates", []):
                await db.execute("INSERT OR REPLACE INTO api_cache VALUES(?,?,?,?)", (entry["cache_key"], entry["source"], json.dumps(entry["response"], ensure_ascii=False), entry["expires_at"]))
            if payload.get("deadline_at") and now_iso() >= payload["deadline_at"]:
                raise AppError(504, "TIMEOUT", "처리시간을 초과했습니다. 다시 시도해 주세요.")
            await db.commit()
            return {"conversation_id": conv_id, "message_id": answer_message}
        except BaseException as exc:
            await db.rollback()
            import asyncio
            if isinstance(exc, (AppError, asyncio.CancelledError)):
                raise
            raise DatabaseError() from exc
        finally:
            await db.close()

    async def get_cache(self, cache_key):
        rows = await self._query("SELECT * FROM api_cache WHERE cache_key=? AND expires_at>?", (cache_key, now_iso()))
        return json.loads(rows[0]["response"]) if rows else None

    async def stats(self):
        result = {}
        for table in ["users", "conversations", "messages", "api_cache"]:
            result[table] = (await self._query(f"SELECT count(*) AS n FROM {table}"))[0]["n"]
        return result

    async def clear_cache(self):
        await self._query("DELETE FROM api_cache", write=True)
