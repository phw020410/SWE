from app.privacy import md_text, safe_url

SOURCE_NAMES = {"WORK24": "고용24", "YOUTH_JOB": "청년 일자리 지원 서비스"}


def render_recommendations(items, plan):
    allowed = {x["external_id"]: x for x in items}
    ordered = []
    seen = set()
    for key in [*plan.selected_ids, *(x["external_id"] for x in items)]:
        if key in allowed and key not in seen:
            ordered.append(allowed[key])
            seen.add(key)
    intro = {"INTEREST_MATCH": "말씀하신 관심 분야와 관련된 부산 교육·채용 정보입니다.",
             "ROLE_MATCH": "말씀하신 직무와 관련된 부산 교육·채용 정보입니다.", "RECENT": "부산 교육·채용 정보를 원천에서 제공하는 날짜순으로 안내합니다."}[plan.reason]
    lines = [intro, ""]
    for kind, label in [("TRAINING", "교육·훈련"), ("JOB", "채용")]:
        group = [x for x in ordered if x["item_type"] == kind]
        if not group:
            continue
        lines += [f"## {label}", ""]
        for item in group:
            lines += [f'### {md_text(item["title"])}', f'- 기관: {md_text(item["organization"])}',
                      f'- 지역: {md_text(item["region"])}']
            if item.get("published_at"):
                lines.append(f'- 공시 시작일: {item["published_at"]}')
            if item.get("starts_at"):
                lines.append(f'- 훈련 시작일: {item["starts_at"]}')
            if item.get("ends_at"):
                lines.append(f'- 종료·마감일: {item["ends_at"]}')
            for key, value in item["raw_data"].items():
                if value:
                    lines.append(f'- {md_text(key)}: {md_text(value)}')
            url = safe_url(item.get("url"))
            label_source = SOURCE_NAMES[item["source"]]
            lines.append(f'- 출처: [{label_source}]({url.replace(chr(40), "%28").replace(chr(41), "%29")})' if url else f'- 출처: {label_source} (원문 링크 미제공)')
            lines.append(f'- [제공기관 이용조건]({item["terms_url"]})')
            lines.append("")
    lines.append("지원 가능 여부와 상세 일정·조건은 원문에서 최종 확인해 주세요.")
    return "\n".join(lines), ordered


def render_image(analysis, plan):
    labels = {"region": "지역", "job_role": "직무", "qualifications": "지원 자격", "application_method": "신청·지원 방법",
              "selection_process": "전형 절차", "target_audience": "참여 대상", "curriculum": "교육과정",
              "required_documents": "지원 서류", "reception_method": "접수 방법"}
    required = (["job_role", "qualifications", "application_method", "selection_process"] if analysis.image_type == "JOB_POSTING"
                else ["target_audience", "curriculum", "application_method", "required_documents", "reception_method"])
    fields = list(dict.fromkeys(["region", *(f for f in plan.fields if f in labels), *required]))
    lines = [f"## {md_text(analysis.title)}", "", "출처: 업로드 이미지 분석 결과", ""]
    lines += [f"- {labels[key]}: {md_text(getattr(analysis, key))}" for key in fields]
    lines += ["", "이미지에서 확인되지 않는 항목은 ‘확인되지 않음’으로 표시했습니다. 원본과 대조해 주세요."]
    return "\n".join(lines)


def export_markdown(conversation):
    lines = [f'# {md_text(conversation["title"] or "대화 내역")}', "", f'대화 ID: {conversation["id"]}', ""]
    for message in conversation.get("messages", []):
        lines += ["---", "", "## 사용자" if message["role"] == "USER" else "## 안내", "", message["content"], ""]
    return "\n".join(lines)
