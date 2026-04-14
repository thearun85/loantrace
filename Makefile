.PHONY: fmt lint typecheck test check clean

lint:
	poetry run ruff check loantrace tests

fmt:
	poetry run ruff format loantrace tests
	poetry run ruff check --fix loantrace tests

typecheck:
	poetry run mypy loantrace tests

test:
	poetry run pytest -v -s

check: fmt lint typecheck test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
