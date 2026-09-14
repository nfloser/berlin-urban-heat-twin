# Data sources

## Berlin Environmental Atlas / Open Data

Three official WFS services are configured:

- Klimaanalysekarten 2022 — `https://gdi.berlin.de/services/wfs/ua_klimaanalyse_2022`
- Klimabewertungskarten 2022 — `https://gdi.berlin.de/services/wfs/ua_klimabewertung_2022`
- Umweltgerechtigkeit 2023/2024 — `https://gdi.berlin.de/services/wfs/ua_umweltgerechtigkeit2023`

The adapter runs `GetCapabilities` before ingestion and can validate a selected feature type through `DescribeFeatureType`. It does not assume a fixed schema. Retrieved feature IDs, layer names, attributes, CRS information and provenance are retained.

Official documentation for the climate-analysis product includes variables such as air/surface temperature, cooling rate, PET, UTCI and urban-heat-island attributes; the climate-assessment product includes official day/night assessment fields. Availability is still verified from the live WFS schema before use. These values remain `official_modelled` and are never presented as current observations.

## DWD Climate Data Center

The observation adapter uses the DWD recent hourly 2 m air-temperature / relative-humidity product. Station metadata are retrieved at runtime; validity intervals and the Berlin bounding box are used instead of a permanent station list.

DWD missing sentinels `-999` and `-9999` become null. Product timestamps are normalized to timezone-aware UTC. Temperature and humidity are validated against explicit domain ranges by the Pydantic model. Raw units are represented by normalized field names (`air_temperature_c`, `relative_humidity_pct`) and the live validation reports them explicitly.

## Source-state policy

- Berlin WFS climate products: `official_modelled`.
- DWD station observations: `observed`.
- Project summaries: `derived`.
- Caller stress tests: `scenario`.

No project component is allowed to collapse those states into a generic "heat value" without provenance.

## Data policy

Large third-party datasets are not committed. Runtime cache content lives in `data/cache`; CI audits that repository-tracked cache payloads are absent. Source licences remain with the providers.