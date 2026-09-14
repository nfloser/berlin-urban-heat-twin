# Testing

The repository uses Red → Green → Refactor boundaries. Tests are colocated by behaviour rather than implementation detail.

Run backend tests:

```bash
pytest
```

Run frontend tests/build:

```bash
cd frontend
npm test
npm run build
```

Full developer gate:

```bash
make quality
```

Provider tests use fixtures only. Production code contains no synthetic meteorological measurements. Fixtures are explicitly confined to `tests/fixtures`.
