# Berlin Urban Heat Twin

A research-oriented urban heat digital twin for Berlin that combines official urban-climate information with genuine meteorological observations while preserving scientific provenance and uncertainty.

The project is **not** a street- or building-level physical simulation. It explicitly distinguishes:

- **MEASURED** — meteorological observations such as DWD station temperature and humidity.
- **OFFICIALLY MODELLED** — Berlin Environmental Atlas climate-analysis and climate-assessment layers.
- **DERIVED** — transparent statistics calculated by this project without spatially inventing measurements.
- **HYPOTHETICAL** — caller-supplied stress-test scenarios, never forecasts.

## Research questions

The system supports questions about structurally heat-burdened areas, the interaction of recent measured weather with official climate patterns, spatial concentrations of thermal burden and interoperable heat context for resilience, energy, mobility and environmental analyses.

## Architecture

```text
Berlin WFS ──► provider ──► validated GeoJSON ──┐
                                               ├──► Heat service ──► FastAPI ──► UI / integration
DWD CDC ─────► provider ──► observations ──────┘
                                  │
                                  └──► transparent derived summaries / scenarios
```

Provider adapters are isolated from domain and analytics logic. API interchange uses EPSG:4326; projected CRS are required for metric geometry operations.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
pytest
uvicorn berlin_heat_twin.api:app --reload
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

Docker:

```bash
docker compose up --build
```

OpenAPI is available at `/docs`; the research UI is served at `/ui/` when `frontend/dist` exists.

## Real-data ingestion

Network access is intentionally not required for unit tests. Live ingestion uses the authoritative source endpoints configured in `berlin_heat_twin.sources`.

```bash
python -m berlin_heat_twin.cli climate-layers climate_analysis
python -m berlin_heat_twin.cli dwd-stations --berlin-only
python -m berlin_heat_twin.cli ingest-dwd --berlin-only
python -m berlin_heat_twin.cli ingest-climate climate_analysis <WFS_TYPE_NAME> --limit 5000
```

The WFS layer name is discovered first rather than hard-coded, because official layer catalogues can change. DWD stations are filtered from current station metadata and validity intervals; no station is assumed active forever.

## API

- `GET /api/v1/health`
- `GET /api/v1/sources`
- `GET /api/v1/climate/layers/{source}`
- `GET /api/v1/heat/state`
- `GET /api/v1/heat/areas`
- `GET /api/v1/weather/stations`
- `GET /api/v1/weather/observations`
- `GET /api/v1/heat/snapshot`
- `POST /api/v1/heat/scenario`

See `docs/integration.md` for stable integration objects.

## Quality

The repository follows test-driven boundaries: parsing, CRS handling, units, missing values, timestamps, classification boundaries, snapshot composition and API contracts are specified in tests. CI runs tests, linting, formatting, typing, frontend tests and frontend build.

## Documentation

- [Architecture](docs/architecture.md)
- [Data sources](docs/data-sources.md)
- [Data model](docs/data-model.md)
- [Heat methodology](docs/heat-methodology.md)
- [Validation](docs/validation.md)
- [Integration](docs/integration.md)
- [Testing](docs/testing.md)
- [Limitations](docs/limitations.md)

## License and source data

Project code is intended for research use. Third-party source data remain governed by their respective licences and terms. Berlin datasets referenced by this project are published through Berlin Open Data; DWD observations are retrieved from the DWD Climate Data Center. Source metadata and provenance are preserved in application objects.
