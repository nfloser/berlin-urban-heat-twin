# Testing

The repository uses Red → Green → Refactor for meaningful behaviour changes. Deterministic tests do not require external network access; provider parsing is fixture-driven, while live availability is checked separately.

Backend gate:

```bash
pytest
ruff check .
ruff format --check .
mypy src
python scripts/repository_audit.py
```

Frontend gate:

```bash
cd frontend
npm test
npm run build
```

Docker gate:

```bash
docker compose config
docker build -t berlin-urban-heat-twin .
```

Live authoritative-source validation:

```bash
python scripts/live_smoke.py
```

Full deterministic developer gate:

```bash
make quality
```

`repository_audit.py` checks required documentation, OpenAPI paths, integration-schema fields, absence of production placeholder markers and absence of committed runtime cache payloads.

Production code contains no generated/synthetic meteorological observations. Synthetic values are confined to explicit unit-test fixtures and objects.