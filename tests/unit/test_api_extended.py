from pathlib import Path

from fastapi.testclient import TestClient

from berlin_heat_twin.api import app
from berlin_heat_twin.domain import ClimateZone, Provenance, StateType
from berlin_heat_twin.service import HeatService


def _zone() -> ClimateZone:
    return ClimateZone(
        zone_id="area.1",
        source_key="climate_assessment",
        layer_type="assessment:test",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [[13.3, 52.5], [13.35, 52.5], [13.35, 52.55], [13.3, 52.55], [13.3, 52.5]]
            ],
        },
        crs="EPSG:4326",
        attributes={"phk_gesamt": "hoch", "bezirk": "Mitte", "pet14h": 36.5},
        provenance=Provenance(
            source="Berlin Open Data / Umweltatlas",
            dataset="fixture",
            source_url="https://example.test",
            state_type=StateType.OFFICIAL_MODELLED,
        ),
    )


def _client(tmp_path: Path) -> TestClient:
    service = HeatService(tmp_path)
    service.cache_climate_layer("climate_assessment", "assessment:test", [_zone()])
    app.state.service = service
    return TestClient(app)


def test_point_polygon_and_classification_queries(tmp_path: Path) -> None:
    client = _client(tmp_path)
    point = client.get("/api/v1/climate/query/point?longitude=13.32&latitude=52.52")
    assert point.status_code == 200
    assert point.json()[0]["attributes"]["phk_gesamt"] == "hoch"

    polygon = client.post(
        "/api/v1/climate/query/polygon",
        json={
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[13.31, 52.51], [13.33, 52.51], [13.33, 52.53], [13.31, 52.53], [13.31, 52.51]]
                ],
            },
            "crs": "EPSG:4326",
        },
    )
    assert polygon.status_code == 200
    assert polygon.json()[0]["zone_id"] == "area.1"

    selected = client.get("/api/v1/climate/areas/by-classification?attribute=phk_gesamt&value=hoch")
    assert selected.status_code == 200
    assert [item["zone_id"] for item in selected.json()] == ["area.1"]


def test_area_analytics_and_openapi_are_published(tmp_path: Path) -> None:
    client = _client(tmp_path)
    summary = client.get(
        "/api/v1/analytics/area-summary?attribute=phk_gesamt&source_key=climate_assessment"
    )
    assert summary.status_code == 200
    assert summary.json()["state_type"] == "derived"
    assert summary.json()["categories"][0]["category"] == "hoch"

    numeric = client.get(
        "/api/v1/analytics/numeric-summary?attribute=pet14h&unit=degC&source_key=climate_assessment"
    )
    assert numeric.status_code == 200
    assert numeric.json()["median"] == 36.5
    assert numeric.json()["unit"] == "degC"

    grouped = client.get(
        "/api/v1/analytics/grouped-area-summary?classification_attribute=phk_gesamt&group_attribute=bezirk"
    )
    assert grouped.status_code == 200
    assert grouped.json()["groups"][0]["group"] == "Mitte"

    schema = client.get("/openapi.json").json()
    assert "/api/v1/climate/query/point" in schema["paths"]
    assert "/api/v1/analytics/area-summary" in schema["paths"]
    assert "/api/v1/analytics/numeric-summary" in schema["paths"]
    assert "/api/v1/heat/snapshot" in schema["paths"]
