from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from berlin_heat_twin.analytics import apply_temperature_scenario, compose_snapshot
from berlin_heat_twin.domain import (
    ClimateZone,
    HeatSnapshot,
    MeteorologicalObservation,
    MeteorologicalStation,
    ScenarioRequest,
    ScenarioResult,
)
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

    def official_areas(self) -> list[ClimateZone]:
        areas: list[ClimateZone] = []
        for key in ("climate_analysis", "climate_assessment", "environmental_justice"):
            for item in self.store.read(f"areas-{key}", []):
                areas.append(ClimateZone.model_validate(item))
        return areas

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
