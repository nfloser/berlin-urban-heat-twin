from berlin_heat_twin.domain import ClimateZone, Provenance, StateType
from berlin_heat_twin.geo import point_matches_zones, polygon_matches_zones, select_zones


def _prov() -> Provenance:
    return Provenance(
        source="fixture",
        dataset="fixture",
        source_url="https://example.test",
        state_type=StateType.OFFICIAL_MODELLED,
    )


def _zone(zone_id: str, x0: float, classification: str, valid: bool = True) -> ClimateZone:
    return ClimateZone(
        zone_id=zone_id,
        source_key="climate_assessment",
        layer_type="assessment:test",
        geometry={
            "type": "Polygon",
            "coordinates": [[
                [x0, 52.5],
                [x0 + 0.05, 52.5],
                [x0 + 0.05, 52.55],
                [x0, 52.55],
                [x0, 52.5],
            ]],
        },
        crs="EPSG:4326",
        attributes={"phk_gesamt": classification, "bezirk": "Mitte"},
        provenance=_prov(),
        geometry_valid=valid,
    )


def test_point_query_returns_only_valid_intersections() -> None:
    zones = [_zone("a", 13.30, "hoch"), _zone("b", 13.40, "niedrig"), _zone("bad", 13.30, "hoch", False)]
    matches = point_matches_zones(zones, longitude=13.32, latitude=52.52)
    assert [zone.zone_id for zone in matches] == ["a"]


def test_polygon_query_supports_explicit_query_crs() -> None:
    zones = [_zone("a", 13.30, "hoch"), _zone("b", 13.40, "niedrig")]
    query = {
        "type": "Polygon",
        "coordinates": [[[13.34, 52.51], [13.42, 52.51], [13.42, 52.54], [13.34, 52.54], [13.34, 52.51]]],
    }
    matches = polygon_matches_zones(zones, query, "EPSG:4326")
    assert [zone.zone_id for zone in matches] == ["a", "b"]


def test_select_zones_preserves_official_classification() -> None:
    zones = [_zone("a", 13.30, "hoch"), _zone("b", 13.40, "niedrig")]
    matches = select_zones(zones, attribute="phk_gesamt", values={"hoch"})
    assert len(matches) == 1
    assert matches[0].attributes["phk_gesamt"] == "hoch"
