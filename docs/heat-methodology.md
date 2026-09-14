# Heat methodology

## Static official baseline

Berlin Environmental Atlas features remain official model/reference output with their original attributes and source classification. The project does not replace an official class with a home-made severity score.

Spatial baseline operations are:

- climate attributes at a WGS84 point via point-in-polygon;
- official areas intersecting a caller polygon with explicit query CRS;
- exact selection by an existing classification attribute/value;
- area by official category after transformation to `EPSG:25833`;
- grouping by an existing source field (for example an official district field when one is actually present);
- count/min/median/max of numeric official attributes with a caller-supplied unit verified from source methodology.

The numerical summary performs **no reclassification**. The area summary does not dissolve overlapping official features, so overlapping source geometries may overlap in totals; this uncertainty is returned with the result.

## Dynamic measured state

For each active cached DWD station, the most recent observation at or before a requested timestamp is selected. The city-level dynamic indicator is the median of those latest station temperatures. It is `derived`, while each source observation stays `observed`.

This median describes the available station sample. It is not a spatially continuous Berlin temperature field.

Filtered station histories are available by station/time range. A station-climate overlap analysis performs point-in-polygon matching between latest measured station locations and selected official model polygons. It still performs no interpolation.

## PET and UTCI

Dynamic PET/UTCI are not calculated because the current DWD adapter does not ingest every physical input required for a defensible dynamic calculation, especially mean radiant temperature. When an official Berlin layer exposes PET/UTCI attributes, those values are consumed directly as `official_modelled`; the generic numeric summary can summarize them when the correct unit is supplied from official metadata.

## Day/night burden

Official day/night classifications can be compared by selecting the relevant official fields/layers (for example official daytime and nighttime assessment attributes when present). The project preserves those source classifications rather than translating them to an undocumented common scale.

## Historical anomalies

The current DWD adapter intentionally ingests the **recent** hourly product, not a validated multi-year baseline. Therefore long-term temperature anomalies are not computed. Adding them requires a separate historical DWD adapter, a documented climatological reference period and time-aware validation.

## Scenario engine

The scenario engine adds a caller-supplied temperature delta to the derived station-temperature median. It does not mutate official climate layers. Every result is `scenario` and explicitly states that it is hypothetical, not an observation or forecast.