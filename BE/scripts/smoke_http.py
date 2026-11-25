"""실제 HTTP 확인. 켜져 있는 로컬 demo 서버를 대상으로 한다."""
import argparse
import uuid

import httpx

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url, trust_env=False, timeout=12) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        if health.json().get("dataProvider") != "fixture":
            raise SystemExit("이 스크립트는 로컬 demo 모드에서만 사용합니다.")
        assert client.get("/").json() == {"message": "Hello, FastAPI!"}
        assert client.get("/health").json() == health.json()
        credentials = {"email": "http-" + uuid.uuid4().hex[:10] + "@example.com", "password": "LocalSmoke123!"}
        signup = client.post("/api/auth/signup", json={**credentials, "name": "가상 테스트"})
        assert signup.status_code == 201
        login = client.post("/api/auth/login", json=credentials)
        assert login.status_code == 200
        client.headers["Authorization"] = "Bearer " + login.json()["accessToken"]
        response = client.post("/api/query", json={"query": "부산 웹 개발 실습 관련해서 뭐 있는지 알려줘"})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "ok" and len(data["items"]) == 4
        history = client.get("/api/history")
        assert history.status_code == 200 and len(history.json()[0]["messages"]) == 2
        export = client.get(f'/api/history/{data["conversationId"]}/export')
        assert export.status_code == 200 and "## 사용자" in export.text
        assert client.post("/api/auth/logout").status_code == 204
        assert client.get("/api/users/me").status_code == 401
        print("실제 HTTP PASS: 가입 201 → 로그인 200 → 추천 200(교육2·채용2) → 이력/Markdown 200 → 로그아웃 204 → 재요청 401")
