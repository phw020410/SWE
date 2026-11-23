from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")
    app_env: Literal["development", "production", "test"] = "development"
    storage_backend: Literal["sqlite", "supabase"] = "sqlite"
    sqlite_path: str = "./local.db"
    supabase_url: str = ""
    supabase_service_role_key: SecretStr = SecretStr("")
    jwt_secret: SecretStr = SecretStr("")
    jwt_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    ai_provider: Literal["gemini", "mock"] = "gemini"
    data_provider: Literal["live", "fixture"] = "live"
    gemini_api_key: SecretStr = SecretStr("")
    gemini_intent_model: str = "gemini-3.5-flash-lite"
    gemini_answer_model: str = "gemini-3.5-flash-lite"
    gemini_image_model: str = "gemini-3.8-flash"
    work24_auth_key: SecretStr = SecretStr("")
    alio_service_key: SecretStr = SecretStr("")
    work24_api_url: str = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"
    youth_job_api_url: str = "https://opendata.alio.go.kr/new/v1/recruit/list.do"
    youth_job_detail_url: str = "https://opendata.alio.go.kr/new/v1/recruit/detail.do"
    youth_job_auth_param: str = "serviceKey"
    cache_ttl_seconds: int = 21600
    request_timeout_seconds: float = Field(default=10, gt=0, le=10)
    intent_timeout_seconds: float = 10
    answer_timeout_seconds: float = 10
    data_timeout_seconds: float = 3
    max_image_bytes: int = 5 * 1024 * 1024
    cpu_threshold: float = 90
    cpu_high_seconds: float = 5
    cpu_sample_seconds: float = 1
    upstream_pages: int = Field(default=2, ge=1, le=10)
    # 기존 저장소의 /items CRUD는 명시적인 개발 데모에서만 노출한다.
    enable_demo_items: bool = False

    def check_startup(self):
        if len(self.jwt_secret.get_secret_value()) < 32 or "REPLACE" in self.jwt_secret.get_secret_value().upper():
            raise RuntimeError("JWT_SECRET이 필요합니다. 루트의 scripts/configure.py를 먼저 실행하세요.")
        if self.storage_backend == "supabase" and (not self.supabase_url or not self.supabase_service_role_key.get_secret_value()):
            raise RuntimeError("SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY가 필요합니다.")
        if self.app_env == "production" and (self.ai_provider == "mock" or self.data_provider == "fixture"):
            raise RuntimeError("production은 Gemini/live 데이터 모드를 사용해야 합니다.")
