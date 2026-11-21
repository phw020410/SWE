## 현재 BE는 FE UI와 운영 Supabase 없이 단독 실행·테스트할 수 있도록 구성했습니다
## 저장·조회·로그인·권한·실패 처리 같은 BE 동작은 확인했지만, 실제 Gemini·고용24·Supabase를 모두 연결한 통합 검증은 남아 있는 상태입니다.
## 따라서 현 코드에서 DB와 FE에 기대하는 부분(맞춰야하는 부분)을 기록해 놓겠습니다. 


## DB 테이블 || 코드에서 필요로하는 핵심 필드 (아래는 현재 BE 코드 기준의 규격입니다)
users :  id(uuid), email(unique), password_hash, name, role(USER/ADMIN), token_version, created_at, updated_at
conversations : id, user_id→users, title, created_at, updated_at
messages : id, conversation_id→conversations, role(USER/ASSISTANT), message_type(TEXT/IMAGE), content, created_at
recommended_items: id, message_id→messages, item_type(TRAINING/JOB), source(WORK24/YOUTH_JOB), external_id, title, organization, url, raw_data(jsonb), created_at
image_analyses : id, message_id(unique), image_type(JOB_POSTING/TRAINING), extracted_data(jsonb), created_at
api_cache : cache_key(PK), source, response(jsonb), expires_at
revoked_tokens : jti(uuid PK), expires_at

RPC | 인수 (?는 생략가능)
save_chat_turn | p(jsonb): user_id, conversation_id?, query, message_type, answer, items, cache_updates?, image_analysis?, deadline_at
p의 user_id·conversation_id·query·message_type·answer·items·cache_updates·image_analysis·deadline_at을 받는다. 새 대화라면 ID를 생성하고, 이어지는 대화라면 user_id 소유를 확인한다. 사용자 메시지 다음에 답변 메시지가 오도록 안정적인 created_at/정렬 순서를 보장한다. 추천 스냅샷은 답변 메시지에, 이미지 추출은 사용자 메시지에 연결한다.
새 대화/메시지/추천/이미지/캐시 변경을 한 트랜잭션으로 저장한다. 필드 제약·소유권·deadline 오류면 모두 롤백한다. 응답 message_id는 답변 메시지의 ID이다.
```json
{"conversation_id":"생성된 UUID","message_id":"답변 메시지 UUID"}
```
get_chat_history | p_user_id, p_limit=30, p_offset=0, p_conversation_id?
반환은 배열이며 각 대화는 id·user_id·title·created_at·updated_at·messages를 가진다
revoke_access_token | p_jti, p_expires_at
반환 내용은 없다.
admin_stats | 없음
users·conversations·messages·api_cache라는 키에 개수를 반환한다

## FE가 호출할 API
기능 | 요청 | 보내는 값 | 받는 값 (?는 생략가능)
회원가입 | POST /api/auth/signup | email, password, name | 사용자 정보
로그인 | POST /api/auth/login | email, password | accessToken, 사용자 정보
질문 | POST /api/query | query, conversationId?, countPerType? | answer, conversationId, sources, items, status
이미지 분석 | POST /api/image-query | FormData의 file, conversationId? | answer, imageType, extracted
대화 이력 | GET /api/history | limit?, offset? | 대화·메시지 배열
대화 다운로드 | GET /api/history/{conversationId}/export | 대화 ID | Markdown 파일
현재 사용자 | GET /api/users/me | 없음 | 사용자 정보
정보 변경 | PATCH /api/users/me | currentPassword, name?, newPassword? | 사용자 정보
로그아웃 | POST /api/auth/logout | 없음 | 204, 응답 본문 없음

로그인 후 받은 accessToken을 이후 요청의 Authorization: Bearer <토큰> 헤더에 넣어 주세요. 회원가입·로그인·상태 확인에는 토큰이 필요하지 않습니다.
새 대화는 conversationId를 null로 보내고, 이어지는 질문에는 이전 응답의 conversationId를 보내 주세요.
오류 응답은 {code, message, requestId} 형식입니다. 로딩을 종료하고 message를 표시하되 사용자의 입력은 유지해 주세요.
이미지 요청은 JPG/PNG, 최대 5MB이며 FormData로 전송해 주세요.

---BE 실행 터미널 코드--
cd BE
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m scripts.configure --mode demo
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --no-access-log
```
상태·로컬 DB 응답·선택 모드 :http://127.0.0.1:8000/api/health
API 직접 테스트: http://127.0.0.1:8000/docs
백엔드 주소 : http://127.0.0.1:8000

SQLite로 FE DB없이 로컬 테스트.
SQLite를 유지한 채 실제 Gemini·고용24 확인하려면

.\.venv\Scripts\python.exe -m scripts.configure --mode live-local --keys-file "C:\PATH\키.txt" --replace

운영 Supabase로 바꿀 때는 --mode live를 사용.
GEMINI_API_KEY·WORK24_AUTH_KEY와 SUPABASE_URL·SUPABASE_SERVICE_ROLE_KEY가 필요.

