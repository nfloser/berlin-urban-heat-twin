from pathlib import Path

from fastapi.testclient import TestClient

from berlin_heat_twin.api import app
from berlin_heat_twin.service import HeatService


def test_health_and_empty_snapshot_contract(tmp_path: Path) -> None:
    app.state.service = HeatService(tmp_path)
    client = TestClient(app)
    assert client.get("/api/v1/health").json()["status"] == "ok"
    response = client.get("/api/v1/heat/snapshot")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["crs"] == "EPSG:4326"
    assert body["state"]["quality"] == "missing"


def test_scenario_contract(tmp_path: Path) -> None:
    app.state.service = HeatService(tmp_path)
    client = TestClient(app)
    response = client.post("/api/v1/heat/scenario", json={"temperature_delta_c": 2})
    assert response.status_code == 200
    assert response.json()["state_type"] == "scenario"
