# 부산이음 FE (React + TypeScript + Vite)

부산 청년 맞춤형 교육·취업 AI 안내 서비스의 프론트엔드입니다. SRS 6장 목업과 SDD 6장 API 설계를 기준으로 구현했습니다.

## 실행

```powershell
cd FE
npm install
copy .env.example .env.local   # 필요하면 VITE_API_BASE_URL 수정
npm run dev                    # http://localhost:5173
```

BE는 `BE/README.md`대로 `http://127.0.0.1:8000`에서 실행해 두세요. BE의 `CORS_ORIGINS`에 `http://localhost:5173`이 들어 있어야 합니다.

| 명령 | 설명 |
| --- | --- |
| `npm run dev` | 개발 서버 |
| `npm run build` | 타입 검사 후 `dist/` 빌드 |
| `npm run lint` | oxlint |

## 환경변수

| 이름 | 설명 |
| --- | --- |
| `VITE_API_BASE_URL` | 백엔드 주소. 로컬 기본값 `http://127.0.0.1:8000`, 배포 시 Render 주소 |

비밀 키(Gemini, 고용24, Supabase)는 **FE에 넣지 않습니다**. 모두 BE(Render) 환경변수에만 둡니다 (SDD 9장).

## Vercel 배포

- Root Directory: `FE`
- Framework Preset: Vite (Build `npm run build`, Output `dist`)
- Environment Variables: `VITE_API_BASE_URL=https://<render-서비스>.onrender.com`
- `vercel.json`이 모든 경로를 `index.html`로 돌려서 `/chat/...` 같은 주소를 새로고침해도 404가 나지 않습니다.
- 배포 후 Render의 `CORS_ORIGINS`에 Vercel 도메인을 추가해야 합니다. 예: `["https://swe.vercel.app"]`

## 화면 ↔ 요구사항

| 경로 | 화면 | 요구사항 | API |
| --- | --- | --- | --- |
| `/` | 로그인 전 미리보기 | - | - |
| `/login` | UI-01 로그인 | FR-006, FR-008 | API-006 |
| `/signup` | UI-02 회원가입 | FR-005 | API-005 → API-006 |
| `/chat`, `/chat/:id` | UI-03 질의 (텍스트·이미지) | FR-001, FR-002, FR-004 | API-001, API-002 |
| `/history`, `/history/:id` | UI-04 내역 조회 + Markdown 다운로드 | FR-003 | API-003, API-004 |
| `/settings` | 정보 수정 | FR-009 | API-008 |
| 사용자 메뉴 → 로그아웃 | | FR-007 | API-007 |
| `/guide` | 이용 안내 · 데이터 출처 · 개인정보 안내 | SRS 2.4 | - |

## 구조

```
src/
  api/          client.ts(fetch·JWT·오류 처리), endpoints.ts(API-001~008), types.ts
  auth/         AuthContext — 토큰 보관(localStorage), 만료 자동 로그아웃, 401 처리
  conversations/ ConversationsContext — /api/history 를 사이드바·채팅·내역이 공유
  components/   레이아웃, 입력창(Composer), 추천 카드, Markdown(DOMPurify)
  pages/        화면별 컴포넌트
  lib/          날짜 포맷, 이미지 검사, 추천 항목 정규화
```

## BE와 맞춘 동작

- 로그인 응답의 `accessToken`을 저장하고 모든 보호 API에 `Authorization: Bearer` 헤더를 붙입니다. 만료(`expiresIn`)가 되거나 401을 받으면 로그인 화면으로 보냅니다.
- 오류 응답 `{code, message, requestId}`의 `message`를 그대로 보여 주고, **입력한 질문·첨부 이미지는 유지**합니다.
- 새 대화는 `conversationId: null`, 이어지는 질문은 이전 응답의 `conversationId`를 보냅니다.
- 이미지는 JPG/PNG·5MB 이하인지 FE에서 먼저 검사한 뒤 `FormData`로 보냅니다.
- AI 응답 Markdown은 DOMPurify로 정리한 뒤 렌더링합니다 (XSS 방지).
- 비밀번호를 변경하면 BE가 기존 토큰을 무효화하므로 다시 로그인하게 합니다.
- `/api/history`의 추천 항목은 `raw_data`에 항목 전체가 들어 있어 `lib/items.ts`에서 `/api/query` 형식과 맞춥니다.
