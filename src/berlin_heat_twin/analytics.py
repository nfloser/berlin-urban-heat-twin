from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from statistics import median

from berlin_heat_twin.domain import (
    AreaCategoryStatistic,
    AreaGroupSummary,
    AreaSummary,
    ClimateZone,
    GroupedAreaSummary,
    HeatSnapshot,
    HeatState,
    MatchedClimateArea,
    MeteorologicalObservation,
    MeteorologicalStation,
    Provenance,
    QualityFlag,
    ScenarioRequest,
    ScenarioResult,
    StateType,
    StationClimateOverlap,
    ThermalIndicator,
)
from berlin_heat_twin.geo import area_square_metres, point_matches_zones, transform_geometry


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
    active_station_ids = {
        station.station_id for station in stations if station.active_at(timestamp)
    }
    snapshot_stations = [
        station for station in stations if station.station_id in active_station_ids
    ]
    snapshot_observations = [o for o in latest if o.station_id in active_station_ids]
    latest_time = max((o.timestamp for o in snapshot_observations), default=None)
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


def _summary_provenance(attribute: str) -> Provenance:
    return Provenance(
        source="Berlin Urban Heat Twin",
        dataset=f"derived area summary for official attribute {attribute}",
        source_url="internal://derived/area-summary",
        state_type=StateType.DERIVED,
        methodology=(
            "Areas are calculated after geometry transformation to EPSG:25833 and grouped by an existing "
            "official attribute value. No project-specific thermal class is inferred."
        ),
    )


def area_summary(zones: list[ClimateZone], *, attribute: str) -> AreaSummary:
    if not attribute:
        raise ValueError("attribute is required")
    grouped: dict[str, dict[str, float | int]] = defaultdict(lambda: {"count": 0, "area": 0.0})
    skipped_invalid = 0
    skipped_missing = 0
    analysed = 0
    for zone in zones:
        if not zone.geometry_valid:
            skipped_invalid += 1
            continue
        if attribute not in zone.attributes or zone.attributes[attribute] is None:
            skipped_missing += 1
            continue
        try:
            projected = transform_geometry(zone.geometry, zone.crs, "EPSG:25833")
            area_m2 = area_square_metres(projected, "EPSG:25833")
        except Exception:
            skipped_invalid += 1
            continue
        category = str(zone.attributes[attribute])
        grouped[category]["count"] = int(grouped[category]["count"]) + 1
        grouped[category]["area"] = float(grouped[category]["area"]) + area_m2
        analysed += 1
    total_area = sum(float(value["area"]) for value in grouped.values())
    categories = [
        AreaCategoryStatistic(
            category=category,
            feature_count=int(values["count"]),
            area_m2=float(values["area"]),
            fraction_of_analysed_area=(float(values["area"]) / total_area if total_area else 0.0),
        )
        for category, values in sorted(grouped.items())
    ]
    source_keys = {zone.source_key for zone in zones if zone.source_key is not None}
    layer_types = {zone.layer_type for zone in zones if zone.layer_type is not None}
    return AreaSummary(
        generated_at=datetime.now(UTC),
        source_key=next(iter(source_keys)) if len(source_keys) == 1 else None,
        layer_type=next(iter(layer_types)) if len(layer_types) == 1 else None,
        attribute=attribute,
        analysed_feature_count=analysed,
        skipped_invalid_geometries=skipped_invalid,
        skipped_missing_attribute=skipped_missing,
        total_area_m2=total_area,
        categories=categories,
        methodology=(
            "Official feature geometries transformed to EPSG:25833 for square-metre area calculation; "
            "grouped exactly by the requested source attribute without reclassification."
        ),
        provenance=_summary_provenance(attribute),
        uncertainty=[
            "Area totals inherit the geometry and classification assumptions of the selected official layer.",
            "Overlapping source features, if present, are not dissolved and can therefore overlap in totals.",
        ],
    )


def grouped_area_summary(
    zones: list[ClimateZone], *, classification_attribute: str, group_attribute: str
) -> GroupedAreaSummary:
    if not group_attribute:
        raise ValueError("group_attribute is required")
    groups: dict[str, list[ClimateZone]] = defaultdict(list)
    for zone in zones:
        value = zone.attributes.get(group_attribute)
        if value is not None:
            groups[str(value)].append(zone)
    return GroupedAreaSummary(
        generated_at=datetime.now(UTC),
        classification_attribute=classification_attribute,
        group_attribute=group_attribute,
        groups=[
            AreaGroupSummary(group=name, summary=area_summary(group_zones, attribute=classification_attribute))
            for name, group_zones in sorted(groups.items())
        ],
        methodology=(
            "Features are grouped by an existing source attribute and each group is summarised in EPSG:25833. "
            "When the group attribute is an official district field this yields a district-level summary; "
            "district membership is never guessed from names."
        ),
        uncertainty=["Groups exist only where the selected official layer exposes the requested grouping attribute."],
    )


def station_climate_overlap(
    *,
    timestamp: datetime,
    stations: list[MeteorologicalStation],
    observations: list[MeteorologicalObservation],
    zones: list[ClimateZone],
    classification_attribute: str,
) -> list[StationClimateOverlap]:
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    timestamp = timestamp.astimezone(UTC)
    latest = {item.station_id: item for item in latest_per_station(observations, timestamp)}
    result: list[StationClimateOverlap] = []
    for station in stations:
        if not station.active_at(timestamp):
            continue
        observation = latest.get(station.station_id)
        if observation is None:
            continue
        matches = point_matches_zones(
            zones, longitude=station.longitude, latitude=station.latitude
        )
        if not matches:
            continue
        result.append(
            StationClimateOverlap(
                timestamp=observation.timestamp,
                station_id=station.station_id,
                station_name=station.name,
                longitude=station.longitude,
                latitude=station.latitude,
                air_temperature_c=observation.air_temperature_c,
                relative_humidity_pct=observation.relative_humidity_pct,
                observation_quality=observation.quality,
                observation_provenance=observation.provenance,
                matched_areas=[
                    MatchedClimateArea(
                        area_id=zone.zone_id,
                        source_key=zone.source_key,
                        layer_type=zone.layer_type,
                        classification=(
                            None
                            if zone.attributes.get(classification_attribute) is None
                            else str(zone.attributes[classification_attribute])
                        ),
                        provenance=zone.provenance,
                    )
                    for zone in matches
                ],
            )
        )
    return result


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
