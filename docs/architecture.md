# Architecture

The architecture is deliberately layered so that external data peculiarities cannot leak into scientific domain logic.

1. **Providers** retrieve and parse Berlin WFS and DWD CDC products.
2. **Domain models** enforce units, timezone awareness, provenance and epistemic state.
3. **Storage** caches normalized JSON for reproducible API snapshots without requiring live provider availability on every request.
4. **Analytics** calculate only transparent summaries. No continuous live temperature surface is produced.
5. **Service/API** expose versioned integration contracts.
6. **Frontend** renders measured station points and official polygons with explicit provenance labels.

API geometries use EPSG:4326. Metric calculations require an explicitly projected CRS and are rejected for geographic coordinates.

Invalid geometries are flagged rather than silently repaired. Any future repair workflow must record both original and repaired geometry and its method.
