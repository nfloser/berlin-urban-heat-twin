from __future__ import annotations

from datetime import UTC, datetime
from statistics import median

from berlin_heat_twin.domain import (
    ClimateZone,
    HeatSnapshot,
    HeatState,
    MeteorologicalObservation,
    MeteorologicalStation,
    Provenance,
    QualityFlag,
    ScenarioRequest,
    ScenarioResult,
    StateType,
    ThermalIndicator,
)


def classify_value(value: float, boundaries: list[tuple[float, str]]) -> str:
    """Classify using ordered inclusive upper boundaries supplied by the caller/methodology."""
    if not boundaries:
        raise ValueError("at least one boundary is required")
    previous = float("-inf")
    for upper, _ in boundaries:
        if upper <= previous:
            raise ValueError("boundaries must be strictly increasing")
        previous = upper
    for upper, label in boundaries:
        if value <= upper:
            return label
    return boundaries[-1][1]


def latest_per_station(
    observations: list[MeteorologicalObservation], at: datetime
) -> list[MeteorologicalObservation]:
    if at.tzinfo is None:
        raise ValueError("snapshot timestamp must be timezone-aware")
    selected: dict[str, MeteorologicalObservation] = {}
    for observation in observations:
        if observation.timestamp > at:
            continue
        current = selected.get(observation.station_id)
        if current is None or observation.timestamp > current.timestamp:
            selected[observation.station_id] = observation
    return sorted(selected.values(), key=lambda item: item.station_id)


def compose_snapshot(
    *,
    timestamp: datetime,
    stations: list[MeteorologicalStation],
    observations: list[MeteorologicalObservation],
    official_areas: list[ClimateZone],
    stale_after_hours: float = 3.0,
) -> HeatSnapshot:
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    timestamp = timestamp.astimezone(UTC)
    latest = latest_per_station(observations, timestamp)
    temperatures = [o.air_temperature_c for o in latest if o.air_temperature_c is not None]
    indicators: list[ThermalIndicator] = []
    if temperatures:
        provenance = Provenance(
            source="Berlin Urban Heat Twin",
            dataset="latest available DWD station observations",
            source_url="internal://derived/latest-station-summary",
            state_type=StateType.DERIVED,
            methodology="Median across latest available station observations; no spatial interpolation.",
        )
        indicators.append(
            ThermalIndicator(
                name="observed_station_temperature_median",
                value=float(median(temperatures)),
                unit="degC",
                state_type=StateType.DERIVED,
                method="median of latest station observations",
                provenance=provenance,
            )
        )
    latest_time = max((o.timestamp for o in latest), default=None)
    freshness = None if latest_time is None else (timestamp - latest_time).total_seconds() / 3600
    quality = QualityFlag.MISSING if latest_time is None else QualityFlag.VERIFIED
    limitations = [
        "Station observations are point measurements and are not interpolated to an exact city-wide surface.",
        "Official climate layers represent their documented model/reference conditions, not live measurements.",
    ]
    if freshness is not None and freshness > stale_after_hours:
        quality = QualityFlag.STALE
        limitations.append(f"Latest observation is older than {stale_after_hours:g} hours.")
    invalid_geometries = sum(not area.geometry_valid for area in official_areas)
    if invalid_geometries:
        limitations.append(
            f"{invalid_geometries} official feature(s) have invalid geometry and were not silently repaired."
        )
    active_station_ids = {
        station.station_id for station in stations if station.active_at(timestamp)
    }
    snapshot_stations = [
        station for station in stations if station.station_id in active_station_ids
    ]
    snapshot_observations = [o for o in latest if o.station_id in active_station_ids]
    state = HeatState(
        timestamp=timestamp,
        latest_observation_at=latest_time,
        observation_count=len(snapshot_observations),
        official_feature_count=len(official_areas),
        indicators=indicators,
        quality=quality,
        limitations=limitations,
    )
    return HeatSnapshot(
        timestamp=timestamp,
        state=state,
        stations=snapshot_stations,
        observations=snapshot_observations,
        official_areas=official_areas,
        freshness_hours=freshness,
        spatial_coverage="DWD station points plus cached official Berlin climate features; no unvalidated interpolation.",
        uncertainty=limitations.copy(),
    )


def apply_temperature_scenario(snapshot: HeatSnapshot, request: ScenarioRequest) -> ScenarioResult:
    base_indicator = next(
        (i for i in snapshot.state.indicators if i.name == "observed_station_temperature_median"),
        None,
    )
    indicators: list[ThermalIndicator] = []
    if base_indicator is not None and isinstance(base_indicator.value, (int, float)):
        provenance = Provenance(
            source="Berlin Urban Heat Twin scenario engine",
            dataset="caller-defined hypothetical temperature stress test",
            source_url="internal://scenario/temperature-delta",
            state_type=StateType.SCENARIO,
            methodology="Adds caller-supplied delta to the derived observed station median only; official layers are unchanged.",
        )
        indicators.append(
            ThermalIndicator(
                name="scenario_station_temperature_median",
                value=float(base_indicator.value) + request.temperature_delta_c,
                unit="degC",
                state_type=StateType.SCENARIO,
                method=f"base median + {request.temperature_delta_c:+g} degC caller-defined delta",
                provenance=provenance,
            )
        )
    return ScenarioResult(
        generated_at=datetime.now(UTC),
        base_snapshot_timestamp=snapshot.timestamp,
        parameter=request,
        indicators=indicators,
    )
