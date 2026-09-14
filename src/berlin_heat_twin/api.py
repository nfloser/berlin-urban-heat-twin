from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import cast

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from berlin_heat_twin.domain import ScenarioRequest, ScenarioResult, SpatialQueryRequest
from berlin_heat_twin.providers.berlin_wfs import BerlinWFSProvider
from berlin_heat_twin.service import HeatService
from berlin_heat_twin.sources import BERLIN_SOURCES, DWD_DATASET_PAGE

app = FastAPI(
    title="Berlin Urban Heat Twin API",
    version="1.1.0",
    description="Research API separating measured, officially modelled, derived and scenario heat information.",
)
app.state.service = HeatService()


def _service() -> HeatService:
    return cast(HeatService, app.state.service)


def _validate_aware(value: datetime | None, name: str) -> None:
    if value is not None and value.tzinfo is None:
        raise HTTPException(422, f"{name} must include a timezone offset")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "berlin-urban-heat-twin"}


@app.get("/api/v1/sources")
def sources() -> list[dict[str, str | None]]:
    berlin = [
        {
            "key": source.key,
            "title": source.title,
            "url": source.url,
            "dataset_page": source.dataset_page,
            "state_type": source.state_type,
            "licence": source.licence,
        }
        for source in BERLIN_SOURCES.values()
    ]
    berlin.append(
        {
            "key": "dwd_hourly_air_temperature",
            "title": "DWD recent hourly 2 m air temperature and humidity",
            "url": DWD_DATASET_PAGE,
            "dataset_page": DWD_DATASET_PAGE,
            "state_type": "observed",
            "licence": None,
        }
    )
    return berlin


@app.get("/api/v1/climate/layers/{source_key}")
def climate_layers(source_key: str) -> list[dict[str, object]]:
    source = BERLIN_SOURCES.get(source_key)
    if source is None:
        raise HTTPException(404, "unknown climate source")
    try:
        layers = BerlinWFSProvider(source).discover_layers()
    except Exception as exc:
        raise HTTPException(502, f"upstream WFS unavailable: {exc}") from exc
    return [layer.model_dump(mode="json") for layer in layers]


@app.get("/api/v1/climate/areas")
def climate_areas(
    source_key: str | None = Query(default=None),
    layer_type: str | None = Query(default=None),
) -> list[dict[str, object]]:
    return [
        item.model_dump(mode="json")
        for item in _service().official_areas(source_key=source_key, layer_type=layer_type)
    ]


@app.get("/api/v1/climate/query/point")
def climate_query_point(
    longitude: float = Query(ge=-180, le=180),
    latitude: float = Query(ge=-90, le=90),
    source_key: str | None = Query(default=None),
    layer_type: str | None = Query(default=None),
) -> list[dict[str, object]]:
    return [
        item.model_dump(mode="json")
        for item in _service().climate_at_point(
            longitude=longitude,
            latitude=latitude,
            source_key=source_key,
            layer_type=layer_type,
        )
    ]


@app.post("/api/v1/climate/query/polygon")
def climate_query_polygon(request: SpatialQueryRequest) -> list[dict[str, object]]:
    try:
        result = _service().climate_intersecting_polygon(
            request.geometry,
            request.crs,
            source_key=request.source_key,
            layer_type=request.layer_type,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return [item.model_dump(mode="json") for item in result]


@app.get("/api/v1/climate/areas/by-classification")
def climate_areas_by_classification(
    attribute: str,
    value: list[str] = Query(),
    source_key: str | None = Query(default=None),
    layer_type: str | None = Query(default=None),
) -> list[dict[str, object]]:
    if not value:
        raise HTTPException(422, "at least one value is required")
    try:
        result = _service().climate_by_classification(
            attribute=attribute,
            values=set(value),
            source_key=source_key,
            layer_type=layer_type,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return [item.model_dump(mode="json") for item in result]


@app.get("/api/v1/heat/state")
def heat_state(at: datetime | None = Query(default=None)) -> dict[str, object]:
    _validate_aware(at, "at")
    return _service().snapshot(at).state.model_dump(mode="json")


@app.get("/api/v1/heat/areas")
def heat_areas() -> list[dict[str, object]]:
    return [item.model_dump(mode="json") for item in _service().official_areas()]


@app.get("/api/v1/weather/stations")
def weather_stations() -> list[dict[str, object]]:
    return [item.model_dump(mode="json") for item in _service().stations()]


@app.get("/api/v1/weather/observations")
def weather_observations(
    station_id: str | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> list[dict[str, object]]:
    _validate_aware(start, "start")
    _validate_aware(end, "end")
    try:
        result = _service().observation_history(station_id=station_id, start=start, end=end)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return [item.model_dump(mode="json") for item in result]


@app.get("/api/v1/analytics/area-summary")
def analytics_area_summary(
    attribute: str,
    source_key: str | None = Query(default=None),
    layer_type: str | None = Query(default=None),
) -> dict[str, object]:
    return (
        _service()
        .thermal_area_summary(
            attribute=attribute,
            source_key=source_key,
            layer_type=layer_type,
        )
        .model_dump(mode="json")
    )


@app.get("/api/v1/analytics/numeric-summary")
def analytics_numeric_summary(
    attribute: str,
    unit: str,
    source_key: str | None = Query(default=None),
    layer_type: str | None = Query(default=None),
) -> dict[str, object]:
    try:
        result = _service().numeric_thermal_summary(
            attribute=attribute,
            unit=unit,
            source_key=source_key,
            layer_type=layer_type,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return result.model_dump(mode="json")


@app.get("/api/v1/analytics/grouped-area-summary")
def analytics_grouped_area_summary(
    classification_attribute: str,
    group_attribute: str,
    source_key: str | None = Query(default=None),
    layer_type: str | None = Query(default=None),
) -> dict[str, object]:
    return (
        _service()
        .grouped_thermal_area_summary(
            classification_attribute=classification_attribute,
            group_attribute=group_attribute,
            source_key=source_key,
            layer_type=layer_type,
        )
        .model_dump(mode="json")
    )


@app.get("/api/v1/analytics/station-climate-overlap")
def analytics_station_climate_overlap(
    classification_attribute: str,
    at: datetime | None = Query(default=None),
    source_key: str | None = Query(default=None),
    layer_type: str | None = Query(default=None),
) -> list[dict[str, object]]:
    _validate_aware(at, "at")
    return [
        item.model_dump(mode="json")
        for item in _service().overlap(
            classification_attribute=classification_attribute,
            timestamp=at,
            source_key=source_key,
            layer_type=layer_type,
        )
    ]


@app.get("/api/v1/heat/snapshot")
def heat_snapshot(at: datetime | None = Query(default=None)) -> dict[str, object]:
    _validate_aware(at, "at")
    return _service().snapshot(at).model_dump(mode="json")


@app.post("/api/v1/heat/scenario", response_model=ScenarioResult)
def heat_scenario(request: ScenarioRequest) -> ScenarioResult:
    return _service().scenario(request)


ui_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if ui_dir.exists():
    app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")
