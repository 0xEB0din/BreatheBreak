.PHONY: install dev test lint format run clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check breathebreak/ tests/

format:
	ruff format breathebreak/ tests/

run:
	python -m breathebreak

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
