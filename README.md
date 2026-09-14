# Berlin Urban Heat Twin

A research-oriented urban heat digital twin for Berlin that combines genuine meteorological observations with official urban-climate information while preserving provenance, uncertainty and epistemic state.

The project deliberately distinguishes four states throughout models, API and UI:

- **MEASURED (`observed`)** — DWD station observations.
- **OFFICIALLY MODELLED (`official_modelled`)** — Berlin Environmental Atlas / Open Data climate products.
- **DERIVED (`derived`)** — transparent project calculations from those sources.
- **HYPOTHETICAL (`scenario`)** — caller-defined stress tests, never forecasts.

It does **not** fabricate a continuous live Berlin temperature surface from sparse station points and does not dynamically calculate PET/UTCI from incomplete physical inputs.

## What the project supports

- dynamic discovery of Berlin WFS layers and `DescribeFeatureType` schemas;
- ingestion of multiple official layers per source without overwriting previously cached layers;
- DWD station discovery from current metadata and validity periods;
- timezone-aware measured temperature/humidity histories;
- climate attributes at a point and official polygons intersecting a query polygon;
- exact selection of official classification values without reclassification;
- area-by-category statistics in projected `EPSG:25833`;
- grouped summaries using an existing official grouping field, including district-level output when the selected source actually exposes a district field;
- count/min/median/max summaries of numeric official attributes such as PET/UTCI fields when present, with an explicitly supplied source-verified unit;
- point-in-polygon overlap of latest measured station observations with official climate-burden areas, without spatial interpolation;
- caller-defined temperature-delta scenarios clearly labelled `scenario`;
- a versioned FastAPI/OpenAPI interface and an interactive Leaflet research UI.

## Architecture

```text
Berlin WFS ─► capabilities + schema discovery ─► validated GeoJSON ─┐
                                                                  ├─► HeatService ─► FastAPI ─► UI / integrations
DWD CDC ───► station metadata + recent hourly observations ──────┘
                                    │
                                    └─► transparent summaries / scenarios
```

Provider adapters are isolated from domain and analytics logic. API interchange uses `EPSG:4326`; metric area calculations transform explicitly to `EPSG:25833`. Invalid geometries are flagged and skipped where validity is required rather than silently repaired.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
```

## Data discovery and ingestion

```bash
python -m berlin_heat_twin.cli climate-layers climate_analysis
python -m berlin_heat_twin.cli climate-layers climate_assessment
python -m berlin_heat_twin.cli climate-layers environmental_justice
python -m berlin_heat_twin.cli dwd-stations --berlin-only
python -m berlin_heat_twin.cli ingest-dwd --berlin-only
python -m berlin_heat_twin.cli ingest-climate climate_analysis <WFS_TYPE_NAME> --limit 5000
python -m berlin_heat_twin.cli ingest-climate climate_assessment <WFS_TYPE_NAME> --limit 5000
```

There is intentionally **no hidden standalone preprocessing/interpolation stage**. Provider adapters normalize source data during ingestion (missing values, timestamps, provenance and API CRS); derived analytics are calculated explicitly at query time. This is part of the scientific design, not an omitted step.

## Run backend and frontend

```bash
cd frontend
npm test
npm run build
cd ..
uvicorn berlin_heat_twin.api:app --reload
```

The API docs are available at `/docs`; after the frontend build the UI is available at `/ui/`.

Docker:

```bash
docker compose up --build
```

## API

Core versioned routes include:

- `GET /api/v1/health`
- `GET /api/v1/sources`
- `GET /api/v1/climate/layers/{source_key}`
- `GET /api/v1/climate/areas`
- `GET /api/v1/climate/query/point`
- `POST /api/v1/climate/query/polygon`
- `GET /api/v1/climate/areas/by-classification`
- `GET /api/v1/weather/stations`
- `GET /api/v1/weather/observations`
- `GET /api/v1/heat/state`
- `GET /api/v1/heat/areas`
- `GET /api/v1/heat/snapshot`
- `GET /api/v1/analytics/area-summary`
- `GET /api/v1/analytics/numeric-summary`
- `GET /api/v1/analytics/grouped-area-summary`
- `GET /api/v1/analytics/station-climate-overlap`
- `POST /api/v1/heat/scenario`

See `docs/integration.md` for the stable downstream contracts.

## Quality gate

```bash
pytest
ruff check .
ruff format --check .
mypy src
python scripts/repository_audit.py
cd frontend && npm test && npm run build
# from repository root
docker compose config
docker build -t berlin-urban-heat-twin .
python scripts/live_smoke.py  # requires outbound network access
```

`make quality` runs the deterministic backend/frontend/audit gate. CI additionally builds Docker and executes the live Berlin-WFS/DWD smoke validation; external provider failure is kept separate from deterministic correctness.

## Configuration and data policy

Configuration examples live in `.env.example`. No application secret is required for the current public source adapters and no credentials are committed. Third-party datasets are not committed: normalized runtime caches live under `data/cache` and are ignored except for `.gitkeep`.

## Documentation

- [Architecture](docs/architecture.md)
- [Data sources](docs/data-sources.md)
- [Data model](docs/data-model.md)
- [Heat methodology](docs/heat-methodology.md)
- [Validation](docs/validation.md)
- [Integration](docs/integration.md)
- [Testing](docs/testing.md)
- [Limitations](docs/limitations.md)

Third-party source data remain governed by their own licences and terms. Source metadata and provenance are preserved in application objects.