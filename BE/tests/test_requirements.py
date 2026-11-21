import asyncio
import json
import time

import aiosqlite
import jwt
import pytest

from app.errors import AIUnavailable, DataSourceError
from app.health import CPUHealth
from app.schemas import AnswerPlan, ImageAnalysis
from tests.conftest import account, poster


def test_fr005_signup_duplicate_hash_and_fr008_login_failure(environment):
    client, app, ai = environment
    headers = account(client)
    user = client.get("/api/users/me", headers=headers).json()
    assert set(user) == {"userId", "email", "name", "role"}
    async def stored():
        return await app.state.repository.find_user("student@example.com")
    saved = client.portal.call(stored)
    assert saved["password_hash"].startswith("$2b$12$")
    response = client.post("/api/auth/signup", json={"email": user["email"], "password": "Learning123!", "name": "다른 이름"})
    assert response.status_code == 409
    for email in [user["email"], "absent@example.com"]:
        response = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword!"})
        assert response.status_code == 401
        assert response.json()["message"] == "이메일 또는 비밀번호가 올바르지 않습니다."


def test_fr006_jwt_expiration_and_fr007_logout(authenticated):
    client, app, ai, headers = authenticated
    token = headers["Authorization"].split()[1]
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["exp"] - payload["iat"] == 3600
    assert client.get("/api/users/me", headers=headers).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/users/me", headers=headers).status_code == 401
    payload["exp"] = 1
    expired = jwt.encode(payload, app.state.settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert client.get("/api/users/me", headers={"Authorization": "Bearer " + expired}).status_code == 401


def test_fr009_update_name_password_invalidates_old_tokens(authenticated):
    client, app, ai, headers = authenticated
    assert client.patch("/api/users/me", headers=headers, json={"name": "새 이름", "currentPassword": "wrong-password"}).status_code == 400
    result = client.patch("/api/users/me", headers=headers, json={"name": "새 이름", "currentPassword": "Learning123!", "newPassword": "ChangedPass123!"})
    assert result.status_code == 200 and result.json()["name"] == "새 이름"
    assert client.get("/api/users/me", headers=headers).status_code == 401
    assert client.post("/api/auth/login", json={"email": "student@example.com", "password": "ChangedPass123!"}).status_code == 200


def test_fr001_fr002_uc001_two_stage_and_history_snapshot(authenticated):
    client, app, ai, headers = authenticated
    response = client.post("/api/query", headers=headers, json={"query": "부산 웹 개발 실습 관련해서 뭐 있는지 알려줘"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "ok"
    assert len([x for x in data["items"] if x["item_type"] == "TRAINING"]) == 2
    assert len([x for x in data["items"] if x["item_type"] == "JOB"]) == 2
    assert [call[0] for call in ai.calls] == ["intent", "answer"]
    history = client.get("/api/history", headers=headers).json()
    assert len(history) == 1 and len(history[0]["messages"]) == 2
    assert history[0]["messages"][0]["content"].startswith("부산 웹 개발")
    assert len(history[0]["messages"][1]["items"]) == 4
    assert len(data["sources"]) == 4


@pytest.mark.parametrize("query,count,kind", [("부산 백엔드 1개씩", 1, None), ("부산 최신 정보 3개씩", 3, None), ("부산 백엔드 교육만", 2, "TRAINING")])
def test_uc001_requested_count_latest_and_type(authenticated, query, count, kind):
    client, app, ai, headers = authenticated
    response = client.post("/api/query", headers=headers, json={"query": query})
    assert response.status_code == 200
    records = response.json()["items"]
    if kind:
        assert all(x["item_type"] == kind for x in records)
        assert len(records) == count
    else:
        assert len(records) == count * 2


def test_uc001_clarification_no_results_outside_and_follow_up(authenticated):
    client, app, ai, headers = authenticated
    for query, status in [("안녕하세요", "needs_clarification"), ("부산 간호 교육", "no_results"), ("서울 백엔드 추천", "out_of_scope")]:
        response = client.post("/api/query", headers=headers, json={"query": query})
        assert response.json()["status"] == status
    response = client.post("/api/query", headers=headers, json={"query": "부산 백엔드 교육"}).json()
    follow = client.post("/api/query", headers=headers, json={"query": "그중 교육만 1개", "conversationId": response["conversationId"]})
    assert follow.status_code == 200 and follow.json()["conversationId"] == response["conversationId"]
    assert ai.calls[-2][2]  # 후속 질문에 해당 대화의 문맥 전달


def test_fr003_uc003_markdown_export_empty_and_ownership(authenticated):
    client, app, ai, headers = authenticated
    assert client.get("/api/history", headers=headers).json() == []
    turn = client.post("/api/query", headers=headers, json={"query": "부산 백엔드"}).json()
    path = f'/api/history/{turn["conversationId"]}/export'
    export = client.get(path, headers=headers)
    assert export.status_code == 200 and export.headers["content-type"].startswith("text/markdown")
    assert "attachment" in export.headers["content-disposition"]
    assert "## 사용자" in export.text and "고용24" in export.text
    other = account(client, "another@example.com")
    assert client.get("/api/history", headers=other).json() == []
    assert client.get(path, headers=other).status_code == 404
    assert client.post("/api/query", headers=other, json={"query": "백엔드", "conversationId": turn["conversationId"]}).status_code == 404


def test_fr004_uc002_image_two_stages_other_region_and_no_original_file(authenticated):
    client, app, ai, headers = authenticated
    response = client.post("/api/image-query", headers=headers, files={"file": ("poster.png", poster(), "image/png")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["imageType"] == "TRAINING" and data["extracted"]["region"] == "서울"
    assert [x[0] for x in ai.calls] == ["image", "image_answer"]
    history = client.get("/api/history", headers=headers).json()
    assert history[0]["messages"][0]["imageAnalysis"]["extracted_data"]["curriculum"] == "개발 실습"
    assert "poster.png" not in json.dumps(history)


@pytest.mark.parametrize("name,content,mime,code", [("bad.txt", b"x", "text/plain", 415), ("bad.png", b"x", "image/png", 415), ("bad.jpg", None, "image/jpeg", 415), ("huge.png", b"x" * (5 * 1024 * 1024 + 1), "image/png", 413)])
def test_image_type_and_size_errors(authenticated, name, content, mime, code):
    client, app, ai, headers = authenticated
    response = client.post("/api/image-query", headers=headers, files={"file": (name, poster() if content is None else content, mime)})
    assert response.status_code == code
    assert client.get("/api/history", headers=headers).json() == []


def test_image_unrelated_rejected_without_saving(authenticated):
    client, app, ai, headers = authenticated
    async def unrelated(*args):
        return ImageAnalysis(image_type="UNRELATED")
    ai.analyze_image = unrelated
    response = client.post("/api/image-query", headers=headers, files={"file": ("poster.png", poster(), "image/png")})
    assert response.status_code == 422 and response.json()["code"] == "UNRELATED_IMAGE"
    assert client.get("/api/history", headers=headers).json() == []


def test_nfr002_ai_req002_failure_does_not_save_conversations_or_cache(authenticated):
    client, app, ai, headers = authenticated
    async def broken(*args):
        raise AIUnavailable()
    ai.generate_answer = broken
    response = client.post("/api/query", headers=headers, json={"query": "부산 백엔드"})
    assert response.status_code == 503 and response.json()["code"] == "AI_UNAVAILABLE"
    counts = client.portal.call(app.state.repository.stats)
    assert counts["conversations"] == counts["messages"] == counts["api_cache"] == 0


def test_nfr001_deadline_cancels_slow_ai_without_saving(authenticated):
    client, app, ai, headers = authenticated
    app.state.settings.request_timeout_seconds = .4
    async def slow(*args):
        await asyncio.sleep(1)
    ai.analyze_query = slow
    started = time.monotonic()
    response = client.post("/api/query", headers=headers, json={"query": "부산 백엔드"})
    assert response.status_code == 504 and time.monotonic() - started < 1
    assert client.get("/api/history", headers=headers).json() == []


def test_nfr005_logs_and_ai_req003_mask_before_ai_and_store(authenticated, caplog):
    client, app, ai, headers = authenticated
    question = "부산 백엔드 010-1234-5678 contact@example.com 001212-3123456"
    response = client.post("/api/query", headers=headers, json={"query": question})
    assert response.status_code == 200
    history = json.dumps(client.get("/api/history", headers=headers).json(), ensure_ascii=False)
    for secret in ["010-1234-5678", "contact@example.com", "001212-3123456"]:
        assert secret not in ai.calls[0][1] and secret not in history and secret not in caplog.text
    assert "개인정보 가림" in history
    assert response.headers["x-request-id"]


@pytest.mark.parametrize("body", [{"query": " "}, {"query": "x" * 1001}, {"query": "백엔드", "countPerType": 11}, {"query": "백엔드", "userId": "other"}])
def test_invalid_inputs_are_400_and_unauthenticated_is_401(authenticated, body):
    client, app, ai, headers = authenticated
    assert client.post("/api/query", headers=headers, json=body).status_code == 400
    assert client.post("/api/query", json={"query": "부산 백엔드"}).status_code == 401


def test_nfr006_cpu_health_latches_for_render_restart(authenticated):
    client, app, ai, headers = authenticated
    health = app.state.health
    health.observe(91, now=10)
    assert not health.unhealthy
    health.observe(95, now=16)
    assert client.get("/api/health").status_code == 503
    health.observe(20, now=17)
    assert health.unhealthy  # Render가 연속 실패를 확인할 때까지 유지


def test_cache_reuse_and_admin_roles(authenticated):
    client, app, ai, headers = authenticated
    first = client.post("/api/query", headers=headers, json={"query": "부산 백엔드"})
    second = client.post("/api/query", headers=headers, json={"query": "부산 백엔드"})
    assert first.status_code == second.status_code == 200
    assert any("캐시" in n for n in second.json()["notices"])
    assert client.get("/api/admin/stats", headers=headers).status_code == 403
    uid = client.get("/api/users/me", headers=headers).json()["userId"]
    async def promote():
        return await app.state.repository.update_user(uid, {"role": "ADMIN"})
    client.portal.call(promote)
    assert client.get("/api/admin/stats", headers=headers).status_code == 200
    assert client.delete("/api/admin/cache", headers=headers).status_code == 204


def test_database_save_failure_rolls_back_existing_data(authenticated):
    client, app, ai, headers = authenticated
    original = app.state.repository.save_turn
    async def invalid(payload):
        payload["items"] = [{"item_type": "JOB"}]  # 메시지 삽입 뒤 레코드 저장이 실패하는 상황
        return await original(payload)
    app.state.repository.save_turn = invalid
    response = client.post("/api/query", headers=headers, json={"query": "부산 백엔드"})
    assert response.status_code == 500
    assert client.get("/api/history", headers=headers).json() == []


def test_cors_allows_only_configured_origin_and_markdown_context_ids(authenticated):
    client, app, ai, headers = authenticated
    response = client.options("/api/query", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.options("/api/query", headers={"Origin": "https://unknown.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in response.headers
