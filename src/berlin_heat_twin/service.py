from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from berlin_heat_twin.analytics import (
    apply_temperature_scenario,
    area_summary,
    compose_snapshot,
    grouped_area_summary,
    station_climate_overlap,
)
from berlin_heat_twin.domain import (
    AreaSummary,
    ClimateZone,
    GroupedAreaSummary,
    HeatSnapshot,
    MeteorologicalObservation,
    MeteorologicalStation,
    ScenarioRequest,
    ScenarioResult,
    StationClimateOverlap,
)
from berlin_heat_twin.geo import point_matches_zones, polygon_matches_zones, select_zones
from berlin_heat_twin.storage import JSONStore


class HeatService:
    def __init__(self, data_dir: str | Path | None = None) -> None:
        root: str | Path = (
            data_dir if data_dir is not None else os.getenv("HEAT_TWIN_DATA_DIR", "data/cache")
        )
        self.store = JSONStore(root)

    def stations(self) -> list[MeteorologicalStation]:
        return [
            MeteorologicalStation.model_validate(item) for item in self.store.read("stations", [])
        ]

    def observations(self) -> list[MeteorologicalObservation]:
        return [
            MeteorologicalObservation.model_validate(item)
            for item in self.store.read("observations", [])
        ]

    def observation_history(
        self,
        *,
        station_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MeteorologicalObservation]:
        for value, name in ((start, "start"), (end, "end")):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if start is not None:
            start = start.astimezone(UTC)
        if end is not None:
            end = end.astimezone(UTC)
        if start is not None and end is not None and start > end:
            raise ValueError("start must not be after end")
        normalized_station = station_id.zfill(5) if station_id is not None else None
        result = [
            item
            for item in self.observations()
            if (normalized_station is None or item.station_id == normalized_station)
            and (start is None or item.timestamp >= start)
            and (end is None or item.timestamp <= end)
        ]
        return sorted(result, key=lambda item: (item.timestamp, item.station_id))

    def official_areas(
        self, *, source_key: str | None = None, layer_type: str | None = None
    ) -> list[ClimateZone]:
        areas: list[ClimateZone] = []
        keys = (
            (source_key,)
            if source_key is not None
            else ("climate_analysis", "climate_assessment", "environmental_justice")
        )
        for key in keys:
            for item in self.store.read(f"areas-{key}", []):
                zone = ClimateZone.model_validate(item)
                if zone.source_key is None:
                    zone = zone.model_copy(update={"source_key": key})
                if layer_type is None or zone.layer_type == layer_type:
                    areas.append(zone)
        return areas

    def climate_at_point(
        self,
        *,
        longitude: float,
        latitude: float,
        source_key: str | None = None,
        layer_type: str | None = None,
    ) -> list[ClimateZone]:
        return point_matches_zones(
            self.official_areas(source_key=source_key, layer_type=layer_type),
            longitude=longitude,
            latitude=latitude,
        )

    def climate_intersecting_polygon(
        self,
        geometry: dict[str, Any],
        crs: str,
        *,
        source_key: str | None = None,
        layer_type: str | None = None,
    ) -> list[ClimateZone]:
        return polygon_matches_zones(
            self.official_areas(source_key=source_key, layer_type=layer_type),
            geometry,
            crs,
        )

    def climate_by_classification(
        self,
        *,
        attribute: str,
        values: set[str],
        source_key: str | None = None,
        layer_type: str | None = None,
    ) -> list[ClimateZone]:
        return select_zones(
            self.official_areas(source_key=source_key, layer_type=layer_type),
            attribute=attribute,
            values=values,
        )

    def thermal_area_summary(
        self,
        *,
        attribute: str,
        source_key: str | None = None,
        layer_type: str | None = None,
    ) -> AreaSummary:
        return area_summary(
            self.official_areas(source_key=source_key, layer_type=layer_type),
            attribute=attribute,
        )

    def grouped_thermal_area_summary(
        self,
        *,
        classification_attribute: str,
        group_attribute: str,
        source_key: str | None = None,
        layer_type: str | None = None,
    ) -> GroupedAreaSummary:
        return grouped_area_summary(
            self.official_areas(source_key=source_key, layer_type=layer_type),
            classification_attribute=classification_attribute,
            group_attribute=group_attribute,
        )

    def overlap(
        self,
        *,
        classification_attribute: str,
        timestamp: datetime | None = None,
        source_key: str | None = None,
        layer_type: str | None = None,
    ) -> list[StationClimateOverlap]:
        return station_climate_overlap(
            timestamp=timestamp or datetime.now(UTC),
            stations=self.stations(),
            observations=self.observations(),
            zones=self.official_areas(source_key=source_key, layer_type=layer_type),
            classification_attribute=classification_attribute,
        )

    def snapshot(self, timestamp: datetime | None = None) -> HeatSnapshot:
        return compose_snapshot(
            timestamp=timestamp or datetime.now(UTC),
            stations=self.stations(),
            observations=self.observations(),
            official_areas=self.official_areas(),
        )

    def scenario(
        self, request: ScenarioRequest, timestamp: datetime | None = None
    ) -> ScenarioResult:
        return apply_temperature_scenario(self.snapshot(timestamp), request)

    def cache_models(self, key: str, values: list[Any]) -> Path:
        return self.store.write(key, [value.model_dump(mode="json") for value in values])

    def cache_climate_layer(
        self, source_key: str, layer_type: str, values: list[ClimateZone]
    ) -> Path:
        existing = self.official_areas(source_key=source_key)
        retained = [zone for zone in existing if zone.layer_type != layer_type]
        normalized = [
            zone.model_copy(update={"source_key": source_key, "layer_type": layer_type})
            for zone in values
        ]
        return self.cache_models(f"areas-{source_key}", retained + normalized)
