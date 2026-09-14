# Data model

Every scientific object preserves provenance and one of four epistemic states: `observed`, `official_modelled`, `derived`, or `scenario`.

Core objects:

- `Provenance` — source, dataset, URL, state type, optional licence/retrieval time/method.
- `QualityFlag` — `verified`, `provisional`, `stale`, `missing`, `invalid`.
- `UrbanClimateLayer` — discovered WFS layer metadata.
- `ClimateZone` — official feature ID, source key, layer type, geometry/CRS, untouched source attributes and geometry-validity flag.
- `MeteorologicalStation` — coordinates, elevation, validity interval and provenance.
- `MeteorologicalObservation` — timezone-aware UTC observation with explicit physical-unit field names and quality.
- `ThermalIndicator` — value, unit, state type, method and provenance.
- `HeatState` / `HeatSnapshot` — current cross-source state, freshness, quality, limitations and uncertainty.
- `ThermalArea` — downstream area contract with timestamp, GeoJSON geometry, CRS, typed indicators, state, source, provenance, freshness, quality and uncertainty.
- `AreaSummary` / `GroupedAreaSummary` — derived area-by-category statistics in square metres.
- `NumericAttributeSummary` — derived count/min/median/max of an existing numeric official attribute with an explicitly supplied source-verified unit.
- `StationClimateOverlap` — measured station values spatially matched to official polygons, with both provenances retained.
- `ScenarioRequest` / `ScenarioResult` — caller-controlled hypothetical stress test.

Observation units are explicit in field names (`air_temperature_c`, `wind_speed_m_s`, etc.); derived indicators carry `unit`. Observation and integration timestamps are timezone-aware and normalized to UTC where appropriate.