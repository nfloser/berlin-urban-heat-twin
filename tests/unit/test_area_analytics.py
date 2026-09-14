from datetime import UTC, datetime

from berlin_heat_twin.analytics import area_summary, grouped_area_summary, station_climate_overlap
from berlin_heat_twin.domain import (
    ClimateZone,
    MeteorologicalObservation,
    MeteorologicalStation,
    Provenance,
    StateType,
)


def _prov(state_type: StateType = StateType.OFFICIAL_MODELLED) -> Provenance:
    return Provenance(
        source="fixture",
        dataset="fixture",
        source_url="https://example.test",
        state_type=state_type,
    )


def _zone(zone_id: str, x0: float, classification: str, district: str) -> ClimateZone:
    return ClimateZone(
        zone_id=zone_id,
        source_key="climate_assessment",
        layer_type="assessment:test",
        geometry={
            "type": "Polygon",
            "coordinates": [
                [[x0, 52.5], [x0 + 0.01, 52.5], [x0 + 0.01, 52.51], [x0, 52.51], [x0, 52.5]]
            ],
        },
        crs="EPSG:4326",
        attributes={"phk_gesamt": classification, "bezirk": district},
        provenance=_prov(),
    )


def test_area_summary_calculates_metric_area_by_official_category() -> None:
    summary = area_summary(
        [_zone("1", 13.3, "hoch", "Mitte"), _zone("2", 13.32, "niedrig", "Pankow")],
        attribute="phk_gesamt",
    )
    assert summary.state_type == StateType.DERIVED
    assert summary.analysed_feature_count == 2
    assert {item.category for item in summary.categories} == {"hoch", "niedrig"}
    assert all(item.area_m2 > 0 for item in summary.categories)
    assert "EPSG:25833" in summary.methodology


def test_grouped_summary_can_express_district_level_results_without_inventing_districts() -> None:
    summary = grouped_area_summary(
        [_zone("1", 13.3, "hoch", "Mitte"), _zone("2", 13.32, "niedrig", "Pankow")],
        classification_attribute="phk_gesamt",
        group_attribute="bezirk",
    )
    assert [group.group for group in summary.groups] == ["Mitte", "Pankow"]
    assert summary.group_attribute == "bezirk"


def test_station_overlap_uses_point_observations_without_interpolation() -> None:
    when = datetime(2026, 9, 14, 12, tzinfo=UTC)
    station = MeteorologicalStation(
        station_id="00001",
        name="Berlin fixture",
        latitude=52.505,
        longitude=13.305,
        provenance=_prov(StateType.OBSERVED),
    )
    observation = MeteorologicalObservation(
        station_id="00001",
        timestamp=when,
        air_temperature_c=30,
        relative_humidity_pct=40,
        provenance=_prov(StateType.OBSERVED),
    )
    result = station_climate_overlap(
        timestamp=when,
        stations=[station],
        observations=[observation],
        zones=[_zone("1", 13.3, "hoch", "Mitte")],
        classification_attribute="phk_gesamt",
    )
    assert result[0].station_id == "00001"
    assert result[0].air_temperature_c == 30
    assert result[0].matched_areas[0].classification == "hoch"
    assert "no spatial interpolation" in result[0].methodology.lower()
