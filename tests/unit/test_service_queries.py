from datetime import UTC, datetime, timedelta
from pathlib import Path

from berlin_heat_twin.domain import ClimateZone, MeteorologicalObservation, Provenance, StateType
from berlin_heat_twin.service import HeatService


def _prov() -> Provenance:
    return Provenance(
        source="fixture",
        dataset="fixture",
        source_url="https://example.test",
        state_type=StateType.OFFICIAL_MODELLED,
    )


def _zone(zone_id: str, layer_type: str) -> ClimateZone:
    return ClimateZone(
        zone_id=zone_id,
        source_key="climate_analysis",
        layer_type=layer_type,
        geometry={"type": "Point", "coordinates": [13.4, 52.5]},
        crs="EPSG:4326",
        attributes={"kind": layer_type},
        provenance=_prov(),
    )


def test_cache_climate_layer_preserves_other_layers(tmp_path: Path) -> None:
    service = HeatService(tmp_path)
    service.cache_climate_layer("climate_analysis", "layer:a", [_zone("a", "layer:a")])
    service.cache_climate_layer("climate_analysis", "layer:b", [_zone("b", "layer:b")])
    assert {zone.layer_type for zone in service.official_areas()} == {"layer:a", "layer:b"}
    service.cache_climate_layer("climate_analysis", "layer:a", [_zone("a2", "layer:a")])
    assert {zone.zone_id for zone in service.official_areas()} == {"a2", "b"}


def test_observation_history_filters_and_sorts(tmp_path: Path) -> None:
    service = HeatService(tmp_path)
    base = datetime(2026, 9, 14, 12, tzinfo=UTC)
    observations = [
        MeteorologicalObservation(
            station_id="00001",
            timestamp=base + timedelta(hours=offset),
            air_temperature_c=20 + offset,
            provenance=Provenance(
                source="DWD",
                dataset="fixture",
                source_url="https://example.test",
                state_type=StateType.OBSERVED,
            ),
        )
        for offset in (2, 0, 1)
    ]
    service.cache_models("observations", observations)
    result = service.observation_history(
        station_id="00001",
        start=base,
        end=base + timedelta(hours=1),
    )
    assert [item.timestamp for item in result] == [base, base + timedelta(hours=1)]
