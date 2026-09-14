# Data model

Every scientific object carries provenance and one of four state types:

- `observed`
- `official_modelled`
- `derived`
- `scenario`

Core objects are `ClimateZone`, `MeteorologicalStation`, `MeteorologicalObservation`, `ThermalIndicator`, `HeatState`, `HeatSnapshot`, `ThermalArea`, `Provenance`, `QualityFlag`, and `ScenarioRequest/ScenarioResult`.

Units are encoded in field names for observations (`air_temperature_c`, `wind_speed_m_s`, etc.) and explicitly in `ThermalIndicator.unit`. Observation and snapshot timestamps must be timezone-aware and are normalized to UTC.
