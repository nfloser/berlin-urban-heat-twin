# Integration contract

The Berlin Urban Heat Twin exposes stable JSON structures for downstream Berlin digital-twin projects.

## HeatSnapshot v1.0

Required concepts:

- `timestamp` — timezone-aware snapshot time
- `crs` — API interchange CRS, currently `EPSG:4326`
- `state` — observation counts, official feature counts, transparent indicators, quality and limitations
- `stations` — active station metadata with provenance
- `observations` — latest point observations with explicit units in field names
- `official_areas` — Berlin climate features and untouched source attributes
- `freshness_hours`
- `spatial_coverage`
- `uncertainty`

Downstream systems must not interpret the station median as an interpolated city surface.

## ThermalArea v1.0

`ThermalArea` contains `area_id`, GeoJSON `geometry`, `crs`, indicator values, optional official classification, provenance, quality and uncertainty. Official classifications must remain distinguishable from any future derived indicators.

## Interoperability

For the energy twin, the most defensible initial covariates are measured station temperature/humidity and official climate class with timestamps and quality. For resilience, affected official polygons and their provenance can be consumed directly. Cross-domain causal claims require separate analysis.
