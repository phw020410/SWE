"""저장 기간 가정 A-12: 30일 지난 대화와 만료 캐시·취소 토큰을 운영자가 정리한다."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone

import aiosqlite
import httpx

from app.config import Settings


async def run(days):
    settings = Settings()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    if settings.storage_backend == "sqlite":
        async with aiosqlite.connect(settings.sqlite_path) as db:
            await db.execute("PRAGMA foreign_keys=ON")
            await db.execute("DELETE FROM conversations WHERE updated_at < ?", (cutoff,))
            await db.execute("DELETE FROM api_cache WHERE expires_at < ?", (now,))
            await db.execute("DELETE FROM revoked_tokens WHERE expires_at < ?", (now,))
            await db.commit()
    else:
        from app.repositories.supabase import SupabaseRepository
        async with httpx.AsyncClient() as client:
            repo = SupabaseRepository(settings, client)
            for table, field, value in [("conversations", "updated_at", cutoff), ("api_cache", "expires_at", now), ("revoked_tokens", "expires_at", now)]:
                await repo._call("DELETE", "/" + table, {field: "lt." + value})
    print("설정 기간이 지난 대화와 만료 데이터를 정리했습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--apply", action="store_true", help="대화 데이터 삭제를 명시적으로 실행")
    args = parser.parse_args()
    if not args.apply or args.days < 1:
        raise SystemExit("삭제를 실행하려면 1일 이상의 --days와 --apply를 지정하세요.")
    asyncio.run(run(args.days))
