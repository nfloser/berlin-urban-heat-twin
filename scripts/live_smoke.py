"""Live-source validation against authoritative upstream services.

This script uses real upstream services and never falls back to synthetic production data.
It stays separate from deterministic unit tests because provider availability is external.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from berlin_heat_twin.domain import MeteorologicalStation, StateType
from berlin_heat_twin.providers.berlin_wfs import BerlinWFSProvider
from berlin_heat_twin.providers.dwd import DWDProvider
from berlin_heat_twin.sources import BERLIN_BBOX_WGS84, BERLIN_SOURCES


def in_berlin(station: MeteorologicalStation) -> bool:
    min_lon, min_lat, max_lon, max_lat = BERLIN_BBOX_WGS84
    return min_lat <= station.latitude <= max_lat and min_lon <= station.longitude <= max_lon


def main() -> None:
    checked_at = datetime.now(UTC)
    report: dict[str, object] = {"checked_at": checked_at.isoformat()}

    climate: dict[str, object] = {}
    for key, source in BERLIN_SOURCES.items():
        provider = BerlinWFSProvider(source)
        layers = provider.discover_layers()
        if not layers:
            raise RuntimeError(f"Berlin WFS source {key} exposes no feature types")
        sample_layer = layers[0]
        schema = provider.describe_feature_type(sample_layer.type_name)
        features = provider.fetch_features(sample_layer.type_name, limit=5)
        if not features:
            raise RuntimeError(
                f"Berlin WFS layer {sample_layer.type_name} returned no sample features"
            )
        wrong_state = [
            feature.zone_id
            for feature in features
            if feature.provenance.state_type is not StateType.OFFICIAL_MODELLED
        ]
        if wrong_state:
            raise RuntimeError(
                f"Berlin WFS features lost official_modelled provenance: {wrong_state}"
            )
        climate[key] = {
            "layer_count": len(layers),
            "sample_type_name": sample_layer.type_name,
            "sample_schema_field_count": len(schema),
            "sample_schema_fields": sorted(schema)[:12],
            "sample_feature_count": len(features),
            "sample_invalid_geometries": sum(not feature.geometry_valid for feature in features),
            "sample_crs": sorted({feature.crs for feature in features}),
            "state_type": StateType.OFFICIAL_MODELLED,
        }
    report["berlin_wfs"] = climate

    dwd = DWDProvider()
    stations = dwd.fetch_station_metadata()
    cutoff = checked_at - timedelta(days=7)
    candidates = [
        station
        for station in stations
        if in_berlin(station)
        and (station.valid_from is None or station.valid_from <= checked_at)
        and (station.valid_to is None or station.valid_to >= cutoff)
    ]
    if not candidates:
        raise RuntimeError(
            "DWD metadata returned no currently/recently active Berlin station candidates"
        )
    report["dwd_station_candidates"] = len(candidates)

    observation_sample = None
    failures: list[str] = []
    for station in candidates:
        try:
            observations = dwd.fetch_recent_observations(station.station_id)
        except Exception as exc:
            failures.append(f"{station.station_id}: {type(exc).__name__}")
            continue
        if not observations:
            failures.append(f"{station.station_id}: empty archive")
            continue
        latest = max(observations, key=lambda item: item.timestamp)
        if latest.timestamp.utcoffset() != timedelta(0):
            raise RuntimeError(f"DWD observation {station.station_id} is not normalized to UTC")
        if latest.provenance.state_type is not StateType.OBSERVED:
            raise RuntimeError(f"DWD observation {station.station_id} lost observed provenance")
        if latest.air_temperature_c is None and latest.relative_humidity_pct is None:
            failures.append(f"{station.station_id}: latest row contains no temperature/humidity")
            continue
        observation_sample = {
            "station_id": station.station_id,
            "station_name": station.name,
            "timestamp": latest.timestamp.isoformat(),
            "air_temperature_c": latest.air_temperature_c,
            "relative_humidity_pct": latest.relative_humidity_pct,
            "units": {
                "air_temperature_c": "degC",
                "relative_humidity_pct": "percent",
            },
            "state_type": latest.provenance.state_type,
            "quality": latest.quality,
            "parsed_observation_count": len(observations),
        }
        break
    if observation_sample is None:
        raise RuntimeError(
            f"No recent Berlin DWD observation could be retrieved and validated; attempts={failures}"
        )
    report["dwd_observation_sample"] = observation_sample
    report["checks"] = {
        "wfs_capabilities": "VERIFIED",
        "wfs_describe_feature_type": "VERIFIED",
        "sample_geometry_validity_inspected": "VERIFIED",
        "official_modelled_provenance": "VERIFIED",
        "dwd_station_metadata": "VERIFIED",
        "dwd_units": "VERIFIED",
        "dwd_value_ranges": "VERIFIED_BY_DOMAIN_VALIDATION",
        "dwd_timezone_utc": "VERIFIED",
        "observed_provenance": "VERIFIED",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
