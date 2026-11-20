"""API smoke tests."""

from fastapi.testclient import TestClient

from geoaicubes import __version__
from geoaicubes.api.app import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "geoaicubes-api"
    assert body["version"] == __version__
