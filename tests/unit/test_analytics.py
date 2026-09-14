from datetime import UTC, datetime, timedelta

import pytest

from berlin_heat_twin.analytics import apply_temperature_scenario, classify_value, compose_snapshot
from berlin_heat_twin.domain import (
    MeteorologicalObservation,
    MeteorologicalStation,
    Provenance,
    QualityFlag,
    ScenarioRequest,
    StateType,
)


def prov(state_type: StateType = StateType.OBSERVED) -> Provenance:
    return Provenance(
        source="fixture",
        dataset="fixture",
        source_url="https://example.test",
        state_type=state_type,
    )


def station(station_id: str) -> MeteorologicalStation:
    return MeteorologicalStation(
        station_id=station_id,
        name=station_id,
        latitude=52.5,
        longitude=13.4,
        valid_from=datetime(2020, 1, 1, tzinfo=UTC),
        valid_to=datetime(2030, 1, 1, tzinfo=UTC),
        provenance=prov(),
    )


def obs(station_id: str, when: datetime, temperature: float) -> MeteorologicalObservation:
    return MeteorologicalObservation(
        station_id=station_id,
        timestamp=when,
        air_temperature_c=temperature,
        provenance=prov(),
    )


def test_classification_boundary_is_inclusive_and_ordered() -> None:
    bounds = [(20, "low"), (30, "elevated"), (99, "high")]
    assert classify_value(20, bounds) == "low"
    assert classify_value(20.1, bounds) == "elevated"
    with pytest.raises(ValueError):
        classify_value(5, [(10, "a"), (10, "b")])


def test_snapshot_uses_latest_per_station_without_interpolation() -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=UTC)
    observations = [
        obs("1", now - timedelta(hours=2), 20),
        obs("1", now - timedelta(hours=1), 24),
        obs("2", now - timedelta(hours=1), 30),
    ]
    snap = compose_snapshot(
        timestamp=now,
        stations=[station("1"), station("2")],
        observations=observations,
        official_areas=[],
    )
    assert snap.state.observation_count == 2
    assert snap.state.indicators[0].value == 27
    assert "no unvalidated interpolation" in snap.spatial_coverage.lower()
    assert snap.state.quality == QualityFlag.VERIFIED


def test_snapshot_marks_stale_observations() -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=UTC)
    snap = compose_snapshot(
        timestamp=now,
        stations=[station("1")],
        observations=[obs("1", now - timedelta(hours=4), 25)],
        official_areas=[],
    )
    assert snap.state.quality == QualityFlag.STALE
    assert snap.freshness_hours == 4


def test_scenario_is_labelled_and_does_not_claim_prediction() -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=UTC)
    snap = compose_snapshot(
        timestamp=now, stations=[station("1")], observations=[obs("1", now, 25)], official_areas=[]
    )
    result = apply_temperature_scenario(snap, ScenarioRequest(temperature_delta_c=2))
    assert result.state_type == StateType.SCENARIO
    assert result.indicators[0].value == 27
    assert "not an observation or forecast" in result.statement.lower()
