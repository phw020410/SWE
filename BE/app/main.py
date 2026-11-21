import asyncio
import contextlib
import json
import logging
import uuid
from contextlib import asynccontextmanager
from time import monotonic

import aiosqlite
import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartParser

from app.ai.gemini import GeminiProvider
from app.ai.mock import MockProvider
from app.config import Settings
from app.body_limit import ImageBodyLimitMiddleware
from app.data.public_api import EmploymentApiClient
from app.errors import AppError
from app.health import CPUHealth
from app.observability import request_id
from app.repositories.sqlite import SQLiteRepository
from app.repositories.supabase import SupabaseRepository
from app.routers import auth, chat, items
from app.services.chat import ChatService

log = logging.getLogger("platform")
logging.basicConfig(level=logging.INFO, format="%(message)s")
# HTTP 클라이언트의 URL 로그에는 query 인증키가 포함될 수 있어 비활성화한다.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def create_app(settings=None, repository=None, ai=None, employment=None, transport=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        settings.check_startup()
        async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
            repo = repository or (SupabaseRepository(settings, client) if settings.storage_backend == "supabase" else SQLiteRepository(settings.sqlite_path))
            await repo.initialize()
            provider = ai or (GeminiProvider(settings, client) if settings.ai_provider == "gemini" else MockProvider())
            data = employment or EmploymentApiClient(settings, client, repo)
            app.state.settings, app.state.repository = settings, repo
            app.state.chat = ChatService(settings, repo, provider, data)
            app.state.health = CPUHealth(settings)
            monitor = asyncio.create_task(app.state.health.monitor())
            try:
                yield
            finally:
                monitor.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await monitor

    app = FastAPI(title="SWE FastAPI Demo", version="0.1.0", lifespan=lifespan)
    MultiPartParser.spool_max_size = max(MultiPartParser.spool_max_size, settings.max_image_bytes + 65536)
    app.add_middleware(ImageBodyLimitMiddleware, limit=settings.max_image_bytes + 65536)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID", "Content-Disposition"])

    def error(request, status, code, message):
        return JSONResponse({"code": code, "message": message, "requestId": getattr(request.state, "request_id", "")}, status_code=status,
            headers={"WWW-Authenticate": "Bearer"} if status == 401 else None)

    @app.exception_handler(AppError)
    async def known_error(request, exc):
        log.log(logging.ERROR if exc.status >= 500 else logging.WARNING, json.dumps({"event": "request_error", "code": exc.code,
            "requestId": getattr(request.state, "request_id", "")}, ensure_ascii=False))
        return error(request, exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation(request, exc):
        if request.url.path == "/items" or request.url.path.startswith("/items/"):
            # 기존 학습용 CRUD의 422 계약은 유지한다. 실제 /api 계약은 400이다.
            return await request_validation_exception_handler(request, exc)
        # 입력 본문이나 비밀번호는 오류 응답에도 포함하지 않는다.
        log.warning(json.dumps({"event": "invalid_input", "requestId": getattr(request.state, "request_id", ""),
                               "fields": [".".join(str(v) for v in item["loc"]) for item in exc.errors()]}))
        return error(request, 400, "INVALID_INPUT", "입력 형식과 길이를 확인해 주세요.")

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(request, exc.status_code, "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR", "요청한 경로나 방식을 확인해 주세요.")

    @app.exception_handler(aiosqlite.Error)
    async def sqlite_error(request, exc):
        return error(request, 500, "DB_ERROR", "데이터 처리에 실패했습니다. 다시 시도해 주세요.")

    @app.middleware("http")
    async def middleware(request: Request, call_next):
        start = monotonic()
        request.state.request_id = str(uuid.uuid4())
        request_id.set(request.state.request_id)
        # 업로드 전체의 추가 상한: reverse proxy에서도 별도 제한한다.
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > settings.max_image_bytes + 65536:
            response = error(request, 413, "IMAGE_TOO_LARGE", "JPG, PNG(5MB 이하)만 가능합니다.")
        else:
            try:
                if request.url.path in {"/api/query", "/api/image-query"}:
                    async with asyncio.timeout(settings.request_timeout_seconds):
                        response = await call_next(request)
                else:
                    response = await call_next(request)
            except TimeoutError:
                response = error(request, 504, "TIMEOUT", "처리시간을 초과했습니다. 다시 시도해 주세요.")
            except Exception as exc:
                log.error(json.dumps({"event": "unhandled_error", "errorType": type(exc).__name__, "requestId": request.state.request_id}))
                response = error(request, 500, "INTERNAL_ERROR", "요청을 처리하지 못했습니다. 다시 시도해 주세요.")
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        route = request.scope.get("route")
        log.info(json.dumps({"event": "http_request", "requestId": request.state.request_id, "method": request.method,
            "path": getattr(route, "path", "unmatched"), "status": response.status_code,
            "latencyMs": round((monotonic() - start) * 1000, 1), "userId": getattr(request.state, "user_id", None)}, ensure_ascii=False))
        return response

    @app.get("/")
    async def root():
        return {"message": "Hello, FastAPI!"}

    @app.get("/health", include_in_schema=False)
    @app.get("/api/health", tags=["상태"])
    async def health(request: Request):
        state = request.app.state
        if state.health.unhealthy:
            return JSONResponse({"status": "unhealthy", "reason": "cpu_high"}, status_code=503)
        try:
            async with asyncio.timeout(2):
                await state.repository.ping()
        except (AppError, TimeoutError):
            return JSONResponse({"status": "unhealthy", "reason": "database"}, status_code=503)
        return {"status": "ok", "aiProvider": settings.ai_provider, "dataProvider": settings.data_provider}

    app.include_router(auth.router)
    app.include_router(chat.router)
    if settings.enable_demo_items and settings.app_env != "production":
        app.include_router(items.router)
    return app


app = create_app()
