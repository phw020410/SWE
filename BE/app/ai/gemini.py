import asyncio
import base64
import json
import logging
from time import monotonic

import httpx
from pydantic import ValidationError

from app.ai.prompts import PromptBuilder
from app.errors import AIUnavailable
from app.observability import request_id
from app.schemas import AnswerPlan, ImageAnalysis, ImageAnswer, UserIntent

log = logging.getLogger("platform")


class GeminiProvider:
    def __init__(self, settings, client):
        self.settings, self.client = settings, client

    async def _json(self, model, prompt, parts, schema, seconds):
        if not self.settings.gemini_api_key.get_secret_value():
            raise AIUnavailable()
        start = monotonic()
        # 모델 이름은 URL 경로이므로 제공자 모델 ID 형식만 허용한다.
        import re
        if not re.fullmatch(r"[a-zA-Z0-9._-]+", model):
            raise AIUnavailable()
        payload = {"systemInstruction": {"parts": [{"text": prompt}]},
                   "contents": [{"role": "user", "parts": parts}],
                   "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json",
                                        "responseJsonSchema": schema.model_json_schema(), "maxOutputTokens": 1600}}
        if model.startswith("gemini-3"):
            payload["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "MINIMAL" if "flash-lite" in model else "LOW"}
        # 재시도도 같은 단계 예산을 나눠 사용한다. 외부 전체 응답은 로그에 남기지 않는다.
        try:
            async with asyncio.timeout(seconds):
                for attempt in range(2):
                    try:
                        response = await self.client.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                            headers={"x-goog-api-key": self.settings.gemini_api_key.get_secret_value()}, json=payload,
                            timeout=max(0.1, seconds - (monotonic() - start)))
                        response.raise_for_status()
                        obj = response.json()
                        text = "".join(p.get("text", "") for p in obj["candidates"][0]["content"]["parts"] if not p.get("thought"))
                        return schema.model_validate_json(text)
                    except (httpx.HTTPError, ValidationError, ValueError, KeyError, IndexError, TypeError):
                        remaining = seconds - (monotonic() - start)
                        log.warning(json.dumps({"event": "ai_retry_or_failure", "requestId": request_id.get(), "model": model, "attempt": attempt + 1}))
                        if attempt or remaining < 0.35:
                            raise AIUnavailable()
                        await asyncio.sleep(min(0.1, remaining / 4))
        except TimeoutError as exc:
            raise AIUnavailable() from exc
        finally:
            log.info(json.dumps({"event": "ai_call", "requestId": request_id.get(), "model": model, "latencyMs": round((monotonic() - start) * 1000)}))

    async def analyze_query(self, query, history):
        return await self._json(self.settings.gemini_intent_model, PromptBuilder.intent,
            [{"text": json.dumps({"query": query, "recent_messages": history[-6:]}, ensure_ascii=False)}],
            UserIntent, self.settings.intent_timeout_seconds)

    async def generate_answer(self, query, items, intent):
        return await self._json(self.settings.gemini_answer_model, PromptBuilder.answer,
            [{"text": json.dumps({"query": query, "intent": intent.model_dump(), "context": items}, ensure_ascii=False)}],
            AnswerPlan, self.settings.answer_timeout_seconds)

    async def analyze_image(self, content, mime):
        return await self._json(self.settings.gemini_image_model, PromptBuilder.image,
            [{"inlineData": {"mimeType": mime, "data": base64.b64encode(content).decode()}}, {"text": "교육·채용 정보를 분석해 주세요."}],
            ImageAnalysis, self.settings.intent_timeout_seconds)

    async def generate_image_answer(self, extraction):
        return await self._json(self.settings.gemini_answer_model, PromptBuilder.image_answer,
            [{"text": extraction.model_dump_json()}], ImageAnswer, self.settings.answer_timeout_seconds)
