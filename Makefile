.PHONY: test lint format-check type audit frontend quality live-smoke

test:
	pytest

lint:
	ruff check .

format-check:
	ruff format --check .

type:
	mypy src

audit:
	python scripts/repository_audit.py

frontend:
	cd frontend && npm test && npm run build

live-smoke:
	python scripts/live_smoke.py

quality: test lint format-check type audit frontend
