from fastapi.testclient import TestClient

from app.main import app


def test_identity_and_security_headers_in_development() -> None:
    with TestClient(app) as client:
        response = client.get("/me", headers={"X-Request-ID": "test-request-1"})

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "local"
    assert response.headers["X-Request-ID"] == "test-request-1"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_readiness_checks_database_and_rate_limiter() -> None:
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["database"] == "ok"
