import re

from app.errors import AIUnavailable
from app.schemas import AnswerPlan, ImageAnswer, UserIntent


class MockProvider:
    """명시적으로 선택한 demo 모드 전용. 실제 이미지 인식은 제공하지 않는다."""
    async def analyze_query(self, query, history):
        compact = re.sub(r"\s+", "", query.lower())
        role = next((r for r in ["백엔드", "데이터", "디자인", "간호", "회계"] if r in compact), None)
        interests = [role] if role else []
        if not interests and any(w in compact for w in ["웹", "web", "개발", "서버", "파이썬"]):
            interests = ["개발", "웹"]
        if not interests and history and any(w in compact for w in ["그중", "그거", "다시"]):
            previous = next((m["content"] for m in reversed(history) if m["role"] == "USER"), "")
            for word in ["백엔드", "데이터", "디자인", "웹", "개발"]:
                if word in previous:
                    interests.append(word)
        latest = any(w in compact for w in ["아무", "뭐든", "최신", "최근"]) and not interests
        count_match = re.search(r"(\d+)\s*(?:개|건)", query)
        count = int(count_match[1]) if count_match else 2
        if not 1 <= count <= 10:
            from app.errors import AppError
            raise AppError(400, "INVALID_INPUT", "추천 개수는 1~10개여야 합니다.")
        kinds = ["TRAINING"] if "교육만" in compact else (["JOB"] if "채용만" in compact else ["TRAINING", "JOB"])
        return UserIntent(job_role=role, interests=interests, count=count, kinds=kinds, latest=latest,
            needs_clarification=not interests and not latest,
            outside_busan=any(c in compact for c in ["서울", "대구", "대전", "인천", "울산", "제주"]) and "부산" not in compact,
            experience="ENTRY" if "신입" in query else "ANY")

    async def generate_answer(self, query, items, intent):
        return AnswerPlan(selected_ids=[x["external_id"] for x in items], reason="RECENT" if intent.latest else "INTEREST_MATCH")

    async def analyze_image(self, content, mime):
        raise AIUnavailable()

    async def generate_image_answer(self, extraction):
        return ImageAnswer(fields=list(extraction.model_dump()))
