# SWE FastAPI Demo

간단한 아이템 CRUD API (인메모리 저장소).

## 구조

```
app/
  main.py          # 앱 진입점
  schemas.py       # Pydantic 모델
  routers/items.py # /items CRUD 라우터
tests/
  test_main.py
```

## 실행 (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev app/main.py
```

- API: http://127.0.0.1:8000
- Swagger 문서: http://127.0.0.1:8000/docs

## 테스트

```powershell
pytest
```

## 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 헬로 메시지 |
| GET | `/health` | 헬스 체크 |
| GET | `/items` | 목록 조회 |
| GET | `/items/{id}` | 단건 조회 |
| POST | `/items` | 생성 |
| PATCH | `/items/{id}` | 부분 수정 |
| DELETE | `/items/{id}` | 삭제 |
