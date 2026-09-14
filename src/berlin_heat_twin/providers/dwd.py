from __future__ import annotations

import csv
import io
import re
import zipfile
from datetime import UTC, datetime

import httpx

from berlin_heat_twin.domain import (
    MeteorologicalObservation,
    MeteorologicalStation,
    Provenance,
    QualityFlag,
    StateType,
)
from berlin_heat_twin.sources import DWD_DATASET_PAGE, DWD_RECENT_TU_BASE_URL, DWD_STATION_METADATA_URL

_MISSING = {-999.0, -9999.0}


class DWDProvider:
    def __init__(self, timeout_seconds: float = 30) -> None:
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _provenance(retrieved_at: datetime | None = None) -> Provenance:
        return Provenance(
            source="Deutscher Wetterdienst Climate Data Center (DWD CDC)",
            dataset="Recent hourly station observations of 2 m air temperature and humidity",
            source_url=DWD_DATASET_PAGE,
            state_type=StateType.OBSERVED,
            retrieved_at=retrieved_at,
            methodology="DWD station observations; values and quality metadata are preserved where exposed.",
        )

    @staticmethod
    def parse_station_metadata(text: str) -> list[MeteorologicalStation]:
        stations: list[MeteorologicalStation] = []
        pattern = re.compile(
            r"^\s*(\d+)\s+(\d{8})\s+(\d{8})\s+(-?\d+(?:\.\d+)?)\s+"
            r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(.+?)\s*$"
        )
        provenance = DWDProvider._provenance()
        for line in text.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            station_id, start, end, elevation, lat, lon, name = match.groups()
            stations.append(
                MeteorologicalStation(
                    station_id=station_id.zfill(5),
                    name=name.strip(),
                    latitude=float(lat),
                    longitude=float(lon),
                    elevation_m=float(elevation),
                    valid_from=datetime.strptime(start, "%Y%m%d").replace(tzinfo=UTC),
                    valid_to=datetime.strptime(end, "%Y%m%d").replace(tzinfo=UTC),
                    provenance=provenance,
                )
            )
        return stations

    @staticmethod
    def _value(raw: str | None) -> float | None:
        if raw is None or not raw.strip():
            return None
        value = float(raw.strip())
        return None if value in _MISSING else value

    @staticmethod
    def parse_observation_csv(text: str, retrieved_at: datetime | None = None) -> list[MeteorologicalObservation]:
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        observations: list[MeteorologicalObservation] = []
        provenance = DWDProvider._provenance(retrieved_at)
        for raw_row in reader:
            row = {str(key).strip(): value for key, value in raw_row.items() if key is not None}
            station_id = str(row.get("STATIONS_ID", "")).strip().zfill(5)
            timestamp_raw = str(row.get("MESS_DATUM", "")).strip()
            if not station_id.strip("0") or not timestamp_raw:
                continue
            timestamp = datetime.strptime(timestamp_raw, "%Y%m%d%H").replace(tzinfo=UTC)
            temp = DWDProvider._value(row.get("TT_TU") or row.get("LUFTTEMPERATUR"))
            humidity = DWDProvider._value(row.get("RF_TU") or row.get("REL_FEUCHTE"))
            quality = QualityFlag.MISSING if temp is None and humidity is None else QualityFlag.VERIFIED
            observations.append(
                MeteorologicalObservation(
                    station_id=station_id,
                    timestamp=timestamp,
                    air_temperature_c=temp,
                    relative_humidity_pct=humidity,
                    quality=quality,
                    provenance=provenance,
                )
            )
        return observations

    @staticmethod
    def parse_zip(content: bytes, retrieved_at: datetime | None = None) -> list[MeteorologicalObservation]:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            candidates = [name for name in archive.namelist() if name.lower().startswith("produkt") and name.endswith(".txt")]
            if not candidates:
                raise ValueError("DWD archive contains no produkt*.txt observation file")
            text = archive.read(candidates[0]).decode("latin-1")
        return DWDProvider.parse_observation_csv(text, retrieved_at)

    def fetch_station_metadata(self) -> list[MeteorologicalStation]:
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(DWD_STATION_METADATA_URL)
            response.raise_for_status()
        return self.parse_station_metadata(response.text)

    def fetch_recent_observations(self, station_id: str) -> list[MeteorologicalObservation]:
        normalized = station_id.zfill(5)
        url = f"{DWD_RECENT_TU_BASE_URL}/stundenwerte_TU_{normalized}_akt.zip"
        retrieved_at = datetime.now(UTC)
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        return self.parse_zip(response.content, retrieved_at)
