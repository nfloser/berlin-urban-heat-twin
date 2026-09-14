from datetime import UTC, datetime
from pathlib import Path

from berlin_heat_twin.domain import QualityFlag
from berlin_heat_twin.providers.dwd import DWDProvider

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_station_metadata_parses_validity_and_coordinates() -> None:
    stations = DWDProvider.parse_station_metadata((FIXTURES / "dwd_stations.txt").read_text())
    assert stations[0].station_id == "00403"
    assert stations[0].latitude == 52.4537
    assert stations[0].active_at(datetime(2026, 9, 14, tzinfo=UTC))
    assert not stations[1].active_at(datetime(2026, 9, 14, tzinfo=UTC))


def test_observations_parse_missing_values_and_utc() -> None:
    observations = DWDProvider.parse_observation_csv(
        (FIXTURES / "dwd_observations.txt").read_text()
    )
    assert observations[0].air_temperature_c == 25.1
    assert observations[0].relative_humidity_pct == 48.0
    assert observations[0].timestamp.tzinfo == UTC
    assert observations[1].air_temperature_c is None
    assert observations[1].relative_humidity_pct == 49.0
    assert observations[2].quality == QualityFlag.MISSING
