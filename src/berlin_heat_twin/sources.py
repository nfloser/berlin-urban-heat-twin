from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceConfig:
    key: str
    title: str
    url: str
    dataset_page: str
    state_type: str
    licence: str | None = None


BERLIN_SOURCES: dict[str, SourceConfig] = {
    "climate_analysis": SourceConfig(
        key="climate_analysis",
        title="Klimaanalysekarten 2022 (Umweltatlas)",
        url="https://gdi.berlin.de/services/wfs/ua_klimaanalyse_2022",
        dataset_page="https://daten.berlin.de/datensaetze/klimaanalysekarten-2022-umweltatlas-wfs-255aead2",
        state_type="official_modelled",
        licence="Datenlizenz Deutschland – Zero – Version 2.0",
    ),
    "climate_assessment": SourceConfig(
        key="climate_assessment",
        title="Klimabewertungskarten 2022 (Umweltatlas)",
        url="https://gdi.berlin.de/services/wfs/ua_klimabewertung_2022",
        dataset_page="https://daten.berlin.de/datensaetze/klimabewertungskarten-2022-umweltatlas-wfs-ac0751a2",
        state_type="official_modelled",
        licence="Datenlizenz Deutschland – Zero – Version 2.0",
    ),
    "environmental_justice": SourceConfig(
        key="environmental_justice",
        title="Umweltgerechtigkeit 2023/2024 (Umweltatlas)",
        url="https://gdi.berlin.de/services/wfs/ua_umweltgerechtigkeit2023",
        dataset_page="https://daten.berlin.de/datensaetze/umweltgerechtigkeit-2023-2024-umweltatlas-wfs-2d02ba21",
        state_type="official_modelled",
        licence="Datenlizenz Deutschland – Zero – Version 2.0",
    ),
}

DWD_STATION_METADATA_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
    "hourly/air_temperature/recent/TU_Stundenwerte_Beschreibung_Stationen.txt"
)
DWD_RECENT_TU_BASE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
    "hourly/air_temperature/recent"
)
DWD_DATASET_PAGE = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/"
    "hourly/air_temperature/recent/"
)

BERLIN_BBOX_WGS84 = (13.088, 52.338, 13.761, 52.675)
