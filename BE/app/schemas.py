from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=72)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Signup(Input):
    email: EmailStr
    password: Password
    name: Name

    @field_validator("password")
    @classmethod
    def bcrypt_byte_limit(cls, value):
        if len(value.encode()) > 72:
            raise ValueError("비밀번호는 UTF-8 72바이트 이하여야 합니다.")
        return value


class Login(Signup):
    name: Name | None = None


class Profile(Input):
    name: Name | None = None
    current_password: Password = Field(alias="currentPassword")
    new_password: Password | None = Field(default=None, alias="newPassword")

    @field_validator("current_password", "new_password")
    @classmethod
    def bcrypt_byte_limit(cls, value):
        if value and len(value.encode()) > 72:
            raise ValueError("비밀번호가 너무 깁니다.")
        return value


class Query(Input):
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    conversation_id: str | None = Field(default=None, alias="conversationId")
    count_per_type: int | None = Field(default=None, ge=1, le=10, alias="countPerType")


class UserIntent(Input):
    job_role: str | None = Field(default=None, max_length=80)
    experience: Literal["ENTRY", "EXPERIENCED", "ANY"] = "ANY"
    interests: list[Annotated[str, StringConstraints(min_length=1, max_length=40)]] = Field(default_factory=list, max_length=5)
    count: int = Field(default=2, ge=1, le=10)
    kinds: list[Literal["TRAINING", "JOB"]] = Field(default_factory=lambda: ["TRAINING", "JOB"], min_length=1, max_length=2)
    latest: bool = False
    needs_clarification: bool = False
    outside_busan: bool = False


class RecommendedItem(Input):
    item_type: Literal["TRAINING", "JOB"]
    source: Literal["WORK24", "YOUTH_JOB"]
    external_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    organization: str = Field(default="확인되지 않음", max_length=100)
    url: str | None = Field(default=None, max_length=1000)
    region: str = "부산"
    published_at: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    raw_data: dict = Field(default_factory=dict)
    terms_url: str
    date_basis: str = "등록일"


class AnswerPlan(Input):
    # 생성 모델이 선택한 ID를 근거 목록과 대조하고, 사실 필드는 서버가 원천 값으로 렌더링한다.
    selected_ids: list[str] = Field(default_factory=list, max_length=20)
    reason: Literal["INTEREST_MATCH", "ROLE_MATCH", "RECENT"] = "INTEREST_MATCH"


class ImageAnalysis(Input):
    image_type: Literal["JOB_POSTING", "TRAINING", "UNRELATED"]
    title: str = Field(default="이미지 분석", max_length=200)
    region: str | None = Field(default=None, max_length=100)
    job_role: str | None = Field(default=None, max_length=300)
    qualifications: str | None = Field(default=None, max_length=1500)
    application_method: str | None = Field(default=None, max_length=1500)
    selection_process: str | None = Field(default=None, max_length=1500)
    target_audience: str | None = Field(default=None, max_length=1500)
    curriculum: str | None = Field(default=None, max_length=1500)
    required_documents: str | None = Field(default=None, max_length=1500)
    reception_method: str | None = Field(default=None, max_length=1500)


class ImageAnswer(Input):
    # VLM 추출 데이터에서 실제 존재하는 필드만 2차 모델이 고르도록 한다.
    fields: list[str] = Field(default_factory=list, max_length=10)


class QueryResponse(BaseModel):
    conversationId: str
    answer: str
    sources: list[dict]
    status: str = "ok"
    messageId: str
    items: list[dict] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)


# 기존 /items 학습용 API 모델: 원래 import 경로 유지.


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(..., gt=0)


class ItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(None, gt=0)


class Item(ItemCreate):
    id: int
