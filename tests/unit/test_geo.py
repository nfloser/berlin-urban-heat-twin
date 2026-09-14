import pytest

from berlin_heat_twin.geo import area_square_metres, transform_geometry, validate_geometry


def test_crs_transform_round_trip_point() -> None:
    point = {"type": "Point", "coordinates": [13.405, 52.52]}
    projected = transform_geometry(point, "EPSG:4326", "EPSG:25833")
    restored = transform_geometry(projected, "EPSG:25833", "EPSG:4326")
    assert restored["coordinates"][0] == pytest.approx(13.405, abs=1e-5)
    assert restored["coordinates"][1] == pytest.approx(52.52, abs=1e-5)


def test_metric_area_rejects_geographic_crs() -> None:
    polygon = {"type": "Polygon", "coordinates": [[[13, 52], [14, 52], [14, 53], [13, 53], [13, 52]]]}
    with pytest.raises(ValueError, match="projected CRS"):
        area_square_metres(polygon, "EPSG:4326")


def test_invalid_geometry_is_reported_not_repaired() -> None:
    bow_tie = {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]}
    valid, reason = validate_geometry(bow_tie)
    assert valid is False
    assert reason == "invalid geometry"
