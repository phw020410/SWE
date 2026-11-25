import re
from datetime import date

from app.privacy import mask, safe_url
from app.schemas import RecommendedItem

WORK24_TERMS = "https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do"
ALIO_TERMS = "https://opendata.alio.go.kr/"


def date_value(value):
    text = str(value or "")
    digits = re.sub(r"\D", "", text)[:8]
    if len(digits) == 8:
        try:
            return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8])).isoformat()
        except ValueError:
            pass
    return None


def text(value):
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value or "")


def is_busan(value, code):
    value, code = text(value), text(code)
    return "부산" in value or "R3014" in code or code.startswith("26")


def training(row):
    if not is_busan(row.get("address"), row.get("trngAreaCd")):
        return None
    if not row.get("trprId") or not row.get("title"):
        return None
    return RecommendedItem(item_type="TRAINING", source="WORK24", external_id=f'{row["trprId"]}:{row.get("trprDegr", "1")}',
        title=mask(text(row["title"]))[:200], organization=mask(text(row.get("subTitle")) or "확인되지 않음")[:100],
        url=safe_url(text(row.get("titleLink"))), starts_at=date_value(row.get("traStartDate")), ends_at=date_value(row.get("traEndDate")),
        # 공개 목록에는 등록일이 없다. 시작일을 등록일로 위장하지 않는다.
        published_at=None, date_basis="훈련 시작일 (등록일 미제공)", terms_url=WORK24_TERMS,
        raw_data={"주소": mask(text(row.get("address"))), "훈련대상": mask(text(row.get("trainTarget"))),
                  "훈련비": text(row.get("courseMan")), "자비부담액": text(row.get("realMan")), "NCS": text(row.get("ncsCd"))}).model_dump()


def job(row):
    if not is_busan(row.get("workRgnNmLst"), row.get("workRgnLst")):
        return None
    if not row.get("recrutPblntSn") or not row.get("recrutPbancTtl"):
        return None
    return RecommendedItem(item_type="JOB", source="YOUTH_JOB", external_id=text(row["recrutPblntSn"]),
        title=mask(text(row["recrutPbancTtl"]))[:200], organization=mask(text(row.get("instNm")) or "확인되지 않음")[:100],
        url=safe_url(text(row.get("srcUrl"))), published_at=date_value(row.get("pbancBgngYmd")), ends_at=date_value(row.get("pbancEndYmd")),
        terms_url=ALIO_TERMS, raw_data={"근무지역": text(row.get("workRgnNmLst")), "경력구분": text(row.get("recrutSeNm")),
            "지원자격": mask(text(row.get("aplyQlfcCn"))), "전형절차": mask(text(row.get("scrnprcdrMthdExpln")))}).model_dump()


def rank(items, intent):
    tokens = list(dict.fromkeys([*(intent.interests or []), *([intent.job_role] if intent.job_role else [])]))
    def score(item):
        haystack = (item["title"] + " " + item["organization"] + " " + str(item["raw_data"])).lower()
        return sum(1 for token in tokens if token.lower() in haystack)
    if tokens:
        items = [x for x in items if score(x)]
    if intent.experience == "ENTRY":
        items = [x for x in items if not ("경력" in x["raw_data"].get("경력구분", "") and "신입" not in x["raw_data"].get("경력구분", ""))]
    unique = {(x["source"], x["external_id"]): x for x in items}
    return sorted(unique.values(), key=lambda x: (score(x), x.get("published_at") or x.get("starts_at") or ""), reverse=True)[:intent.count]
