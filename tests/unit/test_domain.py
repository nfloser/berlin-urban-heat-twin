from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from berlin_heat_twin.domain import MeteorologicalObservation, Provenance, StateType


def provenance() -> Provenance:
    return Provenance(
        source="DWD",
        dataset="fixture",
        source_url="https://example.test",
        state_type=StateType.OBSERVED,
    )


def test_observation_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        MeteorologicalObservation(
            station_id="00403",
            timestamp=datetime(2026, 9, 14, 12),
            air_temperature_c=25,
            provenance=provenance(),
        )


def test_observation_rejects_invalid_humidity() -> None:
    with pytest.raises(ValidationError):
        MeteorologicalObservation(
            station_id="00403",
            timestamp=datetime(2026, 9, 14, 12, tzinfo=UTC),
            relative_humidity_pct=101,
            provenance=provenance(),
        )
