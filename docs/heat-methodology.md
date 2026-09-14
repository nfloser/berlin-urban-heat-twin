# Heat methodology

## Static baseline

Berlin Environmental Atlas features remain official model output with their source classifications and attributes. The project does not relabel an official class unless a separately documented derived method is explicitly requested.

## Dynamic state

For each active cached DWD station, the most recent observation at or before the requested snapshot time is selected. The current implementation derives one city-level summary: the **median of latest available station temperatures**. This statistic is deliberately not spatially interpolated.

It therefore describes the available station sample, not an exact Berlin-wide temperature field.

## Thermal indices

The project does **not** calculate PET or UTCI dynamically because the initial DWD ingestion does not provide all required physical inputs, notably mean radiant temperature. Official PET/UTCI attributes may be ingested from Berlin layers when present and remain `official_modelled`.

## Classification

`classify_value` is a generic, tested boundary primitive. No health-risk or thermal-stress thresholds are silently hard-coded. A future methodology must provide and document source-specific boundaries before using that primitive in production.

## Scenarios

The scenario engine applies a caller-supplied temperature delta to the derived station-temperature median. It does not mutate official climate layers and labels the output `scenario` with the explicit statement that it is not an observation or forecast.
