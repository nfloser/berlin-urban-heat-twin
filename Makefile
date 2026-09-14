.PHONY: test lint format-check type frontend quality

test:
	pytest
lint:
	ruff check .
format-check:
	ruff format --check .
type:
	mypy src
frontend:
	cd frontend && npm test && npm run build
quality: test lint format-check type frontend
