from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta

from berlin_heat_twin.domain import MeteorologicalStation
from berlin_heat_twin.providers.berlin_wfs import BerlinWFSProvider
from berlin_heat_twin.providers.dwd import DWDProvider
from berlin_heat_twin.service import HeatService
from berlin_heat_twin.sources import BERLIN_BBOX_WGS84, BERLIN_SOURCES


def _berlin_station(station: MeteorologicalStation) -> bool:
    min_lon, min_lat, max_lon, max_lat = BERLIN_BBOX_WGS84
    latitude = station.latitude
    longitude = station.longitude
    return min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon


def main() -> None:
    parser = argparse.ArgumentParser(prog="berlin-heat-twin")
    sub = parser.add_subparsers(dest="command", required=True)

    layers = sub.add_parser("climate-layers")
    layers.add_argument("source", choices=BERLIN_SOURCES)

    station_cmd = sub.add_parser("dwd-stations")
    station_cmd.add_argument("--berlin-only", action="store_true")

    ingest_dwd = sub.add_parser("ingest-dwd")
    ingest_dwd.add_argument("--berlin-only", action="store_true")

    ingest_climate = sub.add_parser("ingest-climate")
    ingest_climate.add_argument("source", choices=BERLIN_SOURCES)
    ingest_climate.add_argument("type_name")
    ingest_climate.add_argument("--limit", type=int, default=int(os.getenv("HEAT_TWIN_MAX_WFS_FEATURES", "5000")))

    args = parser.parse_args()
    timeout = float(os.getenv("HEAT_TWIN_HTTP_TIMEOUT_SECONDS", "30"))
    service = HeatService()

    if args.command == "climate-layers":
        provider = BerlinWFSProvider(BERLIN_SOURCES[args.source], timeout)
        for layer in provider.discover_layers():
            print(f"{layer.type_name}\t{layer.title or ''}\t{layer.default_crs or ''}")
        return

    if args.command in {"dwd-stations", "ingest-dwd"}:
        provider = DWDProvider(timeout)
        stations = provider.fetch_station_metadata()
        now = datetime.now(UTC)
        recent_cutoff = now - timedelta(days=7)
        stations = [
            s
            for s in stations
            if (s.valid_from is None or s.valid_from <= now)
            and (s.valid_to is None or s.valid_to >= recent_cutoff)
        ]
        if args.berlin_only:
            stations = [s for s in stations if _berlin_station(s)]
        if args.command == "dwd-stations":
            for station in stations:
                print(f"{station.station_id}\t{station.name}\t{station.latitude:.4f}\t{station.longitude:.4f}")
            return
        observations = []
        successful_stations = []
        for station in stations:
            try:
                values = provider.fetch_recent_observations(station.station_id)
            except Exception as exc:
                print(f"SKIP {station.station_id}: {exc}")
                continue
            observations.extend(values)
            successful_stations.append(station)
        service.cache_models("stations", successful_stations)
        service.cache_models("observations", observations)
        print(f"Cached {len(observations)} observations from {len(successful_stations)} active station(s).")
        return

    if args.command == "ingest-climate":
        provider = BerlinWFSProvider(BERLIN_SOURCES[args.source], timeout)
        discovered = {layer.type_name for layer in provider.discover_layers()}
        if args.type_name not in discovered:
            raise SystemExit(f"Layer {args.type_name!r} not present in current WFS capabilities")
        areas = provider.fetch_features(args.type_name, args.limit)
        service.cache_models(f"areas-{args.source}", areas)
        invalid = sum(not area.geometry_valid for area in areas)
        print(f"Cached {len(areas)} feature(s); invalid geometries: {invalid}.")


if __name__ == "__main__":
    main()
