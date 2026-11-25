"""서버 운영자가 명시한 계정만 관리자로 지정한다. 공개 API로는 관리자 가입을 허용하지 않는다."""
import argparse
import asyncio

import httpx

from app.config import Settings
from app.repositories.base import now_iso
from app.repositories.sqlite import SQLiteRepository
from app.repositories.supabase import SupabaseRepository


async def main(email):
    settings = Settings()
    settings.check_startup()
    async with httpx.AsyncClient() as client:
        repo = SupabaseRepository(settings, client) if settings.storage_backend == "supabase" else SQLiteRepository(settings.sqlite_path)
        await repo.initialize()
        user = await repo.find_user(email.lower())
        if not user:
            raise SystemExit("먼저 해당 계정으로 회원가입해 주세요.")
        await repo.update_user(user["id"], {"role": "ADMIN", "updated_at": now_iso()})
        print("지정 계정의 관리자 권한을 설정했습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    asyncio.run(main(parser.parse_args().email))
