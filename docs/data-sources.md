# Data sources

## Berlin Environmental Atlas / Open Data

Three official WFS services are configured and discovered dynamically before layer ingestion:

- Klimaanalysekarten 2022 — `https://gdi.berlin.de/services/wfs/ua_klimaanalyse_2022`
- Klimabewertungskarten 2022 — `https://gdi.berlin.de/services/wfs/ua_klimabewertung_2022`
- Umweltgerechtigkeit 2023/2024 — `https://gdi.berlin.de/services/wfs/ua_umweltgerechtigkeit2023`

The project does not assume that every advertised thematic variable exists in every layer. `GetCapabilities` is parsed first; only retrieved properties are preserved.

Berlin climate products are represented as `official_modelled`, not observed weather. Original attributes remain untouched.

## DWD Climate Data Center

The initial observation adapter uses the DWD recent hourly 2 m air temperature and relative humidity product. Station metadata are retrieved at runtime, validity intervals are respected, and Berlin candidates are selected spatially rather than by a permanent hard-coded station list.

DWD missing-value sentinels `-999` and `-9999` are normalized to null. Timestamps are interpreted as UTC according to the product convention and returned as timezone-aware values.

## Data policy

Source files are not committed by default. Cached normalized data under `data/cache` are ignored. This keeps the repository small and makes acquisition reproducible.
