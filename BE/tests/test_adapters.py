import asyncio
import json

import httpx
import pytest

from app.ai.gemini import GeminiProvider
from app.config import Settings
from app.data.public_api import EmploymentApiClient, parse_work24
from app.errors import AIUnavailable, DataSourceError
from app.repositories.supabase import SupabaseRepository
from app.schemas import UserIntent
from app.services.markdown import render_recommendations


def config(**kwargs):
    return Settings(_env_file=None, jwt_secret="test-only-0123456789-abcdefghijklmnopqrstuvwxyz", **kwargs)


class Cache:
    async def get_cache(self, key):
        return None


@pytest.mark.asyncio
async def test_actual_gemini_wire_format_retry_and_schema_validation():
    seen = []
    def handler(request):
        seen.append(json.loads(request.content))
        assert request.headers["x-goog-api-key"] == "unit-test-key"
        text = "invalid json" if len(seen) == 1 else '{"interests":["웹"],"count":2}'
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        ai = GeminiProvider(config(gemini_api_key="unit-test-key"), client)
        intent = await ai.analyze_query("웹 개발", [])
        assert intent.interests == ["웹"] and len(seen) == 2
        assert seen[0]["generationConfig"]["responseMimeType"] == "application/json"
        assert "responseJsonSchema" in seen[0]["generationConfig"]


@pytest.mark.asyncio
async def test_gemini_failure_is_typed_and_stage_timeout_is_bounded():
    async def slow(request):
        await asyncio.sleep(1)
        return httpx.Response(200, json={})
    async with httpx.AsyncClient(transport=httpx.MockTransport(slow)) as client:
        with pytest.raises(AIUnavailable):
            await GeminiProvider(config(gemini_api_key="test", intent_timeout_seconds=.05), client).analyze_query("웹", [])


@pytest.mark.asyncio
async def test_work24_official_parameters_xml_and_busan_filter():
    def handler(request):
        query = dict(request.url.params)
        assert query["authKey"] == "work24-test" and query["srchTraArea1"] == "26"
        assert len(query["srchTraStDt"]) == 8 and query["sortCol"] == "2"
        return httpx.Response(200, text='<HRDNet><srchList><scn_list><trprId>T1</trprId><trprDegr>1</trprDegr><title>부산 웹 개발</title><subTitle>기관</subTitle><address>부산진구</address><traStartDate>20261201</traStartDate></scn_list><scn_list><trprId>T2</trprId><title>서울 웹 개발</title><address>서울</address></scn_list></srchList></HRDNet>')
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = EmploymentApiClient(config(work24_auth_key="work24-test"), client, Cache())
        records = await adapter._trainings(UserIntent(interests=["웹"]))
        assert len(records) == 1 and records[0]["published_at"] is None
        assert "등록일 미제공" in records[0]["date_basis"]


@pytest.mark.asyncio
async def test_public_gateway_uses_only_its_own_key_and_filters_busan():
    def handler(request):
        params = dict(request.url.params)
        assert params["serviceKey"] == "portal-test" and params["workRgnLst"] == "R3014"
        return httpx.Response(200, json={"resultCode": "00", "totalCount": 2, "result": [
            {"recrutPblntSn": 1, "recrutPbancTtl": "웹 개발 채용", "instNm": "가상 기관", "workRgnLst": "R3014", "workRgnNmLst": "부산", "pbancBgngYmd": "2026-11-10"},
            {"recrutPblntSn": 2, "recrutPbancTtl": "서울 채용", "workRgnLst": "R3010", "workRgnNmLst": "서울"}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = EmploymentApiClient(config(alio_service_key="must-not-forward", data_gokr_service_key="portal-test"), client, Cache())
        records = await adapter._jobs(UserIntent())
        assert len(records) == 1 and records[0]["source"] == "YOUTH_JOB"


@pytest.mark.asyncio
async def test_alio_key_is_not_forwarded_to_a_different_gateway():
    def forbidden(request):
        raise AssertionError("ALIO 키를 다른 게이트웨이에 보내면 안 된다.")
    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
        adapter = EmploymentApiClient(config(alio_service_key="private-issued-alio-key"), client, Cache())
        with pytest.raises(DataSourceError):
            await adapter._jobs(UserIntent())


@pytest.mark.asyncio
async def test_supabase_atomic_rpc_and_server_only_headers():
    def handler(request):
        assert request.headers["apikey"] == "server-test-key"
        assert request.url.path == "/rest/v1/rpc/save_chat_turn"
        payload = json.loads(request.content)
        assert payload["p"]["query"] == "마스킹된 질문"
        return httpx.Response(200, json={"conversation_id": "c", "message_id": "m"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        repo = SupabaseRepository(config(supabase_url="https://test-project.supabase.co", supabase_service_role_key="server-test-key"), client)
        result = await repo.save_turn({"query": "마스킹된 질문"})
        assert result["message_id"] == "m"


def test_grounded_renderer_ignores_unknown_ids_and_cannot_invent_links():
    from app.schemas import AnswerPlan
    item = {"external_id": "known", "item_type": "JOB", "source": "YOUTH_JOB", "title": "원천 제목", "organization": "기관", "region": "부산", "raw_data": {}, "url": "javascript:alert(1)", "terms_url": "https://www.data.go.kr/data/15125273/openapi.do"}
    answer, selected = render_recommendations([item], AnswerPlan(selected_ids=["invented", "known"]))
    assert len(selected) == 1 and "invented" not in answer and "javascript:" not in answer


@pytest.mark.asyncio
async def test_unexpired_cache_avoids_upstream_and_new_cache_has_six_hour_ttl():
    from datetime import datetime, timezone
    records = [{"external_id": "cached", "source": "WORK24"}]
    class ValidCache:
        async def get_cache(self, key):
            return records
    def forbidden(request):
        raise AssertionError("유효 캐시가 있으면 장애 원천을 호출하지 않는다.")
    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
        adapter = EmploymentApiClient(config(), client, ValidCache())
        found, pending, notices = await adapter.search(UserIntent(kinds=["TRAINING"]))
        assert found == records and pending == [] and notices
        adapter = EmploymentApiClient(config(data_provider="fixture"), client, Cache())
        found, pending, _ = await adapter.search(UserIntent(kinds=["TRAINING"], latest=True))
        seconds = (datetime.fromisoformat(pending[0]["expires_at"]) - datetime.now(timezone.utc)).total_seconds()
        assert 21590 < seconds <= 21600
