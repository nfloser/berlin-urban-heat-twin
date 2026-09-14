"""Live-source smoke validation.

This script uses real upstream services. It never falls back to synthetic production data.
It is intentionally separate from deterministic unit tests because provider availability is external.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from berlin_heat_twin.domain import MeteorologicalStation
from berlin_heat_twin.providers.berlin_wfs import BerlinWFSProvider
from berlin_heat_twin.providers.dwd import DWDProvider
from berlin_heat_twin.sources import BERLIN_BBOX_WGS84, BERLIN_SOURCES


def in_berlin(station: MeteorologicalStation) -> bool:
    min_lon, min_lat, max_lon, max_lat = BERLIN_BBOX_WGS84
    return (
        min_lat <= station.latitude <= max_lat
        and min_lon <= station.longitude <= max_lon
    )


def main() -> None:
    report: dict[str, object] = {"checked_at": datetime.now(UTC).isoformat()}

    climate: dict[str, object] = {}
    for key, source in BERLIN_SOURCES.items():
        provider = BerlinWFSProvider(source)
        layers = provider.discover_layers()
        item: dict[str, object] = {"layer_count": len(layers)}
        if layers:
            features = provider.fetch_features(layers[0].type_name, limit=1)
            item["sample_type_name"] = layers[0].type_name
            item["sample_feature_count"] = len(features)
            item["sample_invalid_geometries"] = sum(not f.geometry_valid for f in features)
        climate[key] = item
    report["berlin_wfs"] = climate

    dwd = DWDProvider()
    stations = dwd.fetch_station_metadata()
    cutoff = datetime.now(UTC) - timedelta(days=7)
    candidates = [
        station
        for station in stations
        if in_berlin(station)
        and (station.valid_to is None or station.valid_to >= cutoff)
    ]
    report["dwd_station_candidates"] = len(candidates)
    observation_sample = None
    failures: list[str] = []
    for station in candidates:
        try:
            observations = dwd.fetch_recent_observations(station.station_id)
        except Exception as exc:
            failures.append(f"{station.station_id}: {type(exc).__name__}")
            continue
        if observations:
            latest = observations[-1]
            observation_sample = {
                "station_id": station.station_id,
                "timestamp": latest.timestamp.isoformat(),
                "air_temperature_c": latest.air_temperature_c,
                "relative_humidity_pct": latest.relative_humidity_pct,
                "state_type": latest.provenance.state_type,
            }
            break
    if observation_sample is None:
        raise RuntimeError(f"No recent Berlin DWD observation could be retrieved; attempts={failures}")
    report["dwd_observation_sample"] = observation_sample
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
