import asyncio
import hashlib
import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

import httpx

from app.data.normalizers import job, rank, training
from app.errors import DataSourceError
from app.observability import request_id

log = logging.getLogger("platform")


def list_rows(value, target=None):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if "trprId" in value or "recrutPblntSn" in value:
            return [value]
        if target and target in value:
            node = value[target]
            return node if isinstance(node, list) else ([node] if isinstance(node, dict) else [])
        for key in ["scn_list", "result", "items", "item", "data", "srchList", "HRDNet", "response", "body"]:
            if key in value:
                found = list_rows(value[key], target)
                if found:
                    return found
    return []


def parse_work24(response):
    try:
        obj = response.json()
        if obj.get("errorCode") or obj.get("errorMsg"):
            raise DataSourceError()
        return list_rows(obj)
    except ValueError:
        try:
            root = ET.fromstring(response.content)
            # XML은 대체 응답으로만 처리하며 DTD/외부 entity 문서는 허용하지 않는다.
            if b"<!DOCTYPE" in response.content.upper() or root.find(".//errorMsg") is not None:
                raise DataSourceError()
            return [{child.tag: child.text or "" for child in row} for row in root.findall(".//scn_list")]
        except ET.ParseError as exc:
            raise DataSourceError() from exc


class EmploymentApiClient:
    def __init__(self, settings, client, repository):
        self.settings, self.client, self.repository = settings, client, repository

    async def search(self, intent):
        tasks = [self._one(kind, intent) for kind in intent.kinds]
        groups = await asyncio.gather(*tasks)
        items, pending, notices = [], [], []
        for records, cache_entry, notice in groups:
            items.extend(records)
            if cache_entry:
                pending.append(cache_entry)
            if notice:
                notices.append(notice)
        return items, pending, notices

    async def _one(self, kind, intent):
        source = "WORK24" if kind == "TRAINING" else "YOUTH_JOB"
        signature = json.dumps({"source": source, "intent": intent.model_dump(), "mode": self.settings.data_provider}, sort_keys=True, ensure_ascii=False)
        key = source + ":" + hashlib.sha256(signature.encode()).hexdigest()
        cached = await self.repository.get_cache(key)
        if cached is not None:
            return cached, None, "6시간 이내 캐시 데이터를 사용했습니다."
        if self.settings.data_provider == "fixture":
            records = json.loads((Path(__file__).resolve().parents[2] / "data/demo_items.json").read_text(encoding="utf-8"))
            records = [x for x in records if x["item_type"] == kind]
            notice = "학습용 가상 공고입니다. 실제 신청·지원 정보가 아닙니다."
        else:
            try:
                async with asyncio.timeout(self.settings.data_timeout_seconds):
                    records = await (self._trainings(intent) if kind == "TRAINING" else self._jobs(intent))
            except (httpx.HTTPError, TimeoutError, ValueError, TypeError, KeyError) as exc:
                log.error(json.dumps({"event": "data_source_failure", "requestId": request_id.get(), "source": source, "errorType": type(exc).__name__}))
                raise DataSourceError() from exc
            notice = "훈련 API는 등록일을 제공하지 않아 훈련 시작일로 정렬합니다." if kind == "TRAINING" else ""
        records = rank(records, intent)
        pending = {"cache_key": key, "source": source, "response": records,
                   "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=self.settings.cache_ttl_seconds)).isoformat()}
        return records, pending, notice

    async def _trainings(self, intent):
        auth = self.settings.work24_auth_key.get_secret_value()
        if not auth:
            raise DataSourceError()
        today = date.today()
        # 검색 기간은 명세에 필수이나 사용자 미제공: 오늘~365일 뒤를 기본 가정으로 사용.
        params = {"authKey": auth, "returnType": "JSON", "outType": "1", "pageSize": "100", "pageNum": "1",
                  "srchTraStDt": today.strftime("%Y%m%d"), "srchTraEndDt": (today + timedelta(days=365)).strftime("%Y%m%d"),
                  "srchTraArea1": "26", "sort": "DESC", "sortCol": "2"}
        # 원천 검색어는 하나, 추가 관심분야는 내려받은 결과를 점수화할 때 적용한다.
        if intent.interests:
            params["srchTraProcessNm"] = intent.interests[0]
        result = []
        for page in range(1, self.settings.upstream_pages + 1):
            response = await self.client.get(self.settings.work24_api_url, params={**params, "pageNum": str(page)}, timeout=self.settings.data_timeout_seconds)
            response.raise_for_status()
            rows = parse_work24(response)
            result.extend(item for row in rows if (item := training(row)))
            if len(rows) < 100:
                break
        return result

    async def _jobs(self, intent):
        host = urlsplit(self.settings.youth_job_api_url).hostname
        # 발급 사이트가 다른 키를 임의로 전달하지 않는다. 공공데이터포털용 키는 별도 설정한다.
        if host == "apis.data.go.kr":
            key = self.settings.data_gokr_service_key.get_secret_value()
        elif host == "opendata.alio.go.kr":
            key = self.settings.alio_service_key.get_secret_value()
        else:
            raise DataSourceError()
        if not key:
            raise DataSourceError()
        params = {self.settings.youth_job_auth_param: unquote(key), "resultType": "json", "numOfRows": "100", "pageNo": "1", "workRgnLst": "R3014", "ongoingYn": "Y"}
        if intent.interests:
            params["recrutPbancTtl"] = intent.interests[0]
        if intent.experience == "ENTRY":
            params["recrutSe"] = "R2010,R2030"
        result = []
        for page in range(1, self.settings.upstream_pages + 1):
            response = await self.client.get(self.settings.youth_job_api_url, params={**params, "pageNo": str(page)}, timeout=self.settings.data_timeout_seconds)
            response.raise_for_status()
            obj = response.json()
            if str(obj.get("resultCode", "00")) not in {"00", "0", "200", "NORMAL_SERVICE"}:
                raise DataSourceError()
            rows = list_rows(obj)
            result.extend(item for row in rows if (item := job(row)))
            if len(rows) < 100:
                break
        return result
