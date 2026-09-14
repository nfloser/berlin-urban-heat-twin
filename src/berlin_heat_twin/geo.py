from __future__ import annotations

from typing import Any, cast

from pyproj import CRS, Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform


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
    transformer = Transformer.from_crs(source, target, always_xy=True)
    transformed = transform(transformer.transform, shape(geometry))
    return cast(dict[str, Any], mapping(transformed))


def area_square_metres(geometry: dict[str, Any], crs: str) -> float:
    parsed_crs = CRS.from_user_input(crs)
    if parsed_crs.is_geographic:
        raise ValueError("metric area calculation requires a projected CRS")
    return float(shape(geometry).area)
