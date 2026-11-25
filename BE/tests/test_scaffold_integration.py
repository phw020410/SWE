from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_existing_render_health_alias_reports_real_health(environment):
    client, app, _ = environment
    assert client.get("/health").json() == client.get("/api/health").json()
    app.state.health.observe(95, now=10)
    app.state.health.observe(95, now=16)
    assert client.get("/health").status_code == 503


def test_demo_items_are_disabled_by_default_and_in_production():
    for overrides in [{}, {"app_env": "production", "enable_demo_items": True}]:
        settings = Settings(_env_file=None, **overrides)
        app = create_app(settings)
        assert "/items" not in app.openapi()["paths"]
        # No startup is needed to test that these routes are absent.
        assert TestClient(app).get("/items").status_code == 404


def test_original_demo_items_and_business_api_keep_separate_validation_contracts(environment):
    client, _, _ = environment
    assert client.post("/items", json={"name": "Pen", "price": -1}).status_code == 422
    assert client.post("/api/auth/signup", json={"email": "invalid"}).status_code == 400
