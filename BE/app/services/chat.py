import asyncio
import re
from datetime import datetime, timedelta, timezone

from app.errors import AppError
from app.privacy import mask, mask_tree
from app.schemas import ImageAnalysis, QueryResponse
from app.services.images import validate_image
from app.services.markdown import render_image, render_recommendations


class ChatService:
    def __init__(self, settings, repository, ai, employment):
        self.settings, self.repository, self.ai, self.employment = settings, repository, ai, employment

    async def _context(self, user_id, conversation_id):
        if not conversation_id:
            return []
        # 다른 대화의 문맥을 섞지 않는다. 오래된 대화도 목록 페이지 범위와 무관하게 읽는다.
        conversation = await self.repository.full_conversation(user_id, conversation_id)
        return [{"role": x["role"], "content": x["content"][:1000]} for x in conversation.get("messages", [])[-6:]]

    async def query(self, user, request):
        deadline = datetime.now(timezone.utc) + timedelta(seconds=self.settings.request_timeout_seconds - 0.2)
        async with asyncio.timeout(self.settings.request_timeout_seconds - 0.1):
            question = mask(request.query)
            history = await self._context(user["id"], request.conversation_id)
            intent = await self.ai.analyze_query(question, history)
            intent.interests = list(dict.fromkeys(part.strip() for word in intent.interests
                for part in re.split(r"[/,;|]+", word) if part.strip()))[:5]
            if request.count_per_type is not None:
                intent.count = request.count_per_type
            notices = ["개인정보는 가려서 처리했습니다."] if question != request.query else []
            items, pending, status = [], [], "ok"
            if intent.outside_busan:
                answer, status = "텍스트 추천은 부산 지역의 교육·채용 정보를 제공합니다. 부산에서 찾는 직무나 관심 분야를 알려 주세요.", "out_of_scope"
            elif intent.needs_clarification or not (intent.latest or intent.job_role or intent.interests):
                answer, status = "희망 직무나 관심 분야를 알려 주세요. 예: 부산 웹 개발 교육과 신입 채용을 추천해 줘.", "needs_clarification"
            else:
                items, pending, source_notices = await self.employment.search(intent)
                notices += source_notices
                if not items:
                    answer, status = "조건에 맞는 부산 지역 교육·채용 정보를 찾지 못했습니다. 희망 직무나 관심 분야를 바꿔 다시 질문해 주세요.", "no_results"
                else:
                    plan = await self.ai.generate_answer(question, items, intent)
                    answer, items = render_recommendations(items, plan)
            if self.settings.data_provider == "fixture":
                answer = "**학습용 가상 데이터입니다.**\n\n" + answer
            answer = mask(answer)
            saved = await self.repository.save_turn({"user_id": user["id"], "conversation_id": request.conversation_id,
                "query": question, "message_type": "TEXT", "answer": answer, "items": mask_tree(items),
                "cache_updates": mask_tree(pending), "deadline_at": deadline.isoformat()})
            return QueryResponse(conversationId=saved["conversation_id"], messageId=saved["message_id"], answer=answer,
                sources=[{"source": x["source"], "title": x["title"], "url": x.get("url")} for x in items], items=items,
                notices=list(dict.fromkeys(notices)), status=status)

    async def image(self, user, raw, filename, mime, conversation_id):
        deadline = datetime.now(timezone.utc) + timedelta(seconds=self.settings.request_timeout_seconds - 0.2)
        async with asyncio.timeout(self.settings.request_timeout_seconds - 0.1):
            await self._context(user["id"], conversation_id)
            if len(raw) > self.settings.max_image_bytes:
                raise AppError(413, "IMAGE_TOO_LARGE", "JPG, PNG(5MB 이하)만 가능합니다.")
            content, actual_mime = await asyncio.to_thread(validate_image, raw, filename, mime)
            extraction = await self.ai.analyze_image(content, actual_mime)
            extraction = ImageAnalysis.model_validate(mask_tree(extraction.model_dump()))
            if extraction.image_type == "UNRELATED":
                raise AppError(422, "UNRELATED_IMAGE", "채용·교육훈련 관련 이미지만 분석할 수 있습니다.")
            plan = await self.ai.generate_image_answer(extraction)
            answer = mask(render_image(extraction, plan))
            saved = await self.repository.save_turn({"user_id": user["id"], "conversation_id": conversation_id,
                "query": "[이미지 분석 요청]", "message_type": "IMAGE", "answer": answer, "items": [],
                "image_analysis": extraction.model_dump(), "deadline_at": deadline.isoformat()})
            return {"conversationId": saved["conversation_id"], "messageId": saved["message_id"], "imageType": extraction.image_type,
                    "extracted": extraction.model_dump(), "answer": answer, "sources": [{"source": "UPLOAD", "title": "업로드 이미지 분석 결과", "url": None}]}
