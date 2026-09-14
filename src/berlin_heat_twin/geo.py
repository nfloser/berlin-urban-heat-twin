from __future__ import annotations

from typing import Any

from pyproj import CRS, Transformer
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform

from berlin_heat_twin.domain import ClimateZone


def validate_geometry(geometry: dict[str, Any]) -> tuple[bool, str | None]:
    geom = shape(geometry)
    if geom.is_empty:
        return False, "empty geometry"
    if not geom.is_valid:
        return False, "invalid geometry"
    return True, None


def transform_geometry(
    geometry: dict[str, Any], source_crs: str, target_crs: str
) -> dict[str, Any]:
    if not source_crs or not target_crs:
        raise ValueError("source and target CRS are required")
    source = CRS.from_user_input(source_crs)
    target = CRS.from_user_input(target_crs)
    if source == target:
        return geometry
    transformer = Transformer.from_crs(source, target, always_xy=True)
    transformed = transform(transformer.transform, shape(geometry))
    return mapping(transformed)


def area_square_metres(geometry: dict[str, Any], crs: str) -> float:
    parsed_crs = CRS.from_user_input(crs)
    if parsed_crs.is_geographic:
        raise ValueError("metric area calculation requires a projected CRS")
    return float(shape(geometry).area)


def _usable_zone(zone: ClimateZone) -> bool:
    if not zone.geometry_valid:
        return False
    valid, _ = validate_geometry(zone.geometry)
    return valid


def point_matches_zones(
    zones: list[ClimateZone], *, longitude: float, latitude: float
) -> list[ClimateZone]:
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError("point coordinates must be valid WGS84 longitude/latitude")
    point_geometry: dict[str, Any] = mapping(Point(longitude, latitude))
    matches: list[ClimateZone] = []
    for zone in zones:
        if not _usable_zone(zone):
            continue
        query = transform_geometry(point_geometry, "EPSG:4326", zone.crs)
        if shape(zone.geometry).covers(shape(query)):
            matches.append(zone)
    return matches


def polygon_matches_zones(
    zones: list[ClimateZone], geometry: dict[str, Any], query_crs: str
) -> list[ClimateZone]:
    valid, reason = validate_geometry(geometry)
    if not valid:
        raise ValueError(f"query geometry is not valid: {reason}")
    if shape(geometry).geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError("query geometry must be Polygon or MultiPolygon")
    matches: list[ClimateZone] = []
    for zone in zones:
        if not _usable_zone(zone):
            continue
        query = transform_geometry(geometry, query_crs, zone.crs)
        if shape(zone.geometry).intersects(shape(query)):
            matches.append(zone)
    return matches


def select_zones(
    zones: list[ClimateZone], *, attribute: str, values: set[str]
) -> list[ClimateZone]:
    if not attribute:
        raise ValueError("attribute is required")
    if not values:
        raise ValueError("at least one classification value is required")
    return [
        zone
        for zone in zones
        if attribute in zone.attributes and str(zone.attributes[attribute]) in values
    ]
