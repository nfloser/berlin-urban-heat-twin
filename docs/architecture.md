# Architecture

The architecture separates source acquisition, scientific semantics, analytics and presentation so external provider details cannot silently change the meaning of heat indicators.

1. **Providers** retrieve Berlin WFS capabilities, `DescribeFeatureType` schemas and GeoJSON features, plus DWD station metadata and recent hourly observations.
2. **Domain models** enforce timezone awareness, meteorological ranges, provenance, quality and the four epistemic states.
3. **Storage** caches normalized JSON. Multiple WFS layers from the same official source are retained independently by `layer_type`.
4. **Geospatial services** validate geometry, transform CRS, perform point/polygon intersections and require projected CRS for metric area.
5. **Analytics** calculate only transparent statistics: measured-history filtering, station medians, official-class area totals, numeric source-attribute summaries, grouping by existing source attributes and measured-station/official-area overlap.
6. **Scenario engine** applies caller-defined temperature deltas to the derived station median only and never mutates official layers.
7. **FastAPI/OpenAPI** exposes versioned endpoints and stable integration schemas.
8. **Frontend** renders DWD measurements as points and official model results as polygons with timestamps, provenance and uncertainty labels.

API geometries use `EPSG:4326`. Area calculations transform to `EPSG:25833`. Invalid source geometry is preserved with `geometry_valid=false`; operations that need valid geometry skip it and report that limitation rather than repairing it invisibly.

The project intentionally contains no implicit interpolation layer between DWD points and Berlin-wide polygons.