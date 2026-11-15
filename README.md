사용 언어: Python (FastAPI)<br>
배포 환경<br>
FE: Vercel<br>
BE: Render<br>
DB: Supabase

---
API-005, 006, 009 를 제외한 모든 API 는 Authorization: Bearer \<JWT accessToken> 헤더가 필요함<br>
요청, 응답은 JSON<br>
sources[] 는 {source, title, url} 목록

| API ID | Method | Endpoint | req | res | 추가 설명 |
| --- | --- | --- | --- | --- | --- |
| API-001 | POST | /api/query | query, conversationId? | conversationId, answer, sources[] | req 의 conversationId 는 요청 시, 포함해도 되고 안해도 된다.<br>대화 이어가기용|
| API-002 | POST | /api/image-query | multipart {file(jpg, png)}, (conversationId) | conversationId, imageType, extracted, answer |
| API-003 | GET | /api/history | - | conversationId, title, updatedAt, messages[] |
| API-004 | GET | /api/history/{conversationId}/export | - | text/markdown |
| API-005 | POST | /api/auth/signup | email, password, name | userId, email, name |
| API-006 | POSt | /api/auth/login | email, password | accessToken, tokenType, expiresIn |
| API-007 | POST | /api/auth/logout | - | - |
| API-008 | PATCH | /api/users/me | name?, currentPassword, newPassword? | userId, email, name |
| API-009 | GET | /api/health | - | status |