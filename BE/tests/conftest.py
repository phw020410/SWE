from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.ai.mock import MockProvider
from app.config import Settings
from app.main import create_app
from app.schemas import ImageAnalysis, ImageAnswer


class SpyAI(MockProvider):
    def __init__(self):
        self.calls = []

    async def analyze_query(self, query, history):
        self.calls.append(("intent", query, history))
        return await super().analyze_query(query, history)

    async def generate_answer(self, query, items, intent):
        self.calls.append(("answer", query, items))
        return await super().generate_answer(query, items, intent)

    async def analyze_image(self, content, mime):
        self.calls.append(("image", mime, len(content)))
        return ImageAnalysis(image_type="TRAINING", title="테스트 교육 포스터", region="서울", target_audience="청년", curriculum="개발 실습", reception_method="홈페이지 신청")

    async def generate_image_answer(self, extraction):
        self.calls.append(("image_answer", extraction.image_type))
        return ImageAnswer(fields=["target_audience", "curriculum", "application_method", "required_documents", "reception_method"])


@pytest.fixture
def environment(tmp_path):
    settings = Settings(_env_file=None, app_env="test", sqlite_path=str(tmp_path / "test.db"), storage_backend="sqlite",
        jwt_secret="test-secret-only-not-for-deployment-0123456789", ai_provider="mock", data_provider="fixture",
        enable_demo_items=True)
    ai = SpyAI()
    app = create_app(settings, ai=ai)
    with TestClient(app) as client:
        yield client, app, ai


def account(client, email="student@example.com"):
    credentials = {"email": email, "password": "Learning123!"}
    result = client.post("/api/auth/signup", json={**credentials, "name": "학습자"})
    assert result.status_code == 201, result.text
    result = client.post("/api/auth/login", json=credentials)
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["accessToken"]}


@pytest.fixture
def authenticated(environment):
    client, app, ai = environment
    return client, app, ai, account(client)


def poster():
    output = BytesIO()
    Image.new("RGB", (100, 100), "white").save(output, "PNG")
    return output.getvalue()
