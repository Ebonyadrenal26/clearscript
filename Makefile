.PHONY: help install dev test lint format typecheck clean run docs build

help:
	@echo "clearscript development commands"
	@echo ""
	@echo "  make install     Install runtime dependencies via uv"
	@echo "  make dev         Install dev dependencies"
	@echo "  make test        Run pytest"
	@echo "  make lint        Run ruff lint"
	@echo "  make format      Run ruff format"
	@echo "  make typecheck   Run mypy"
	@echo "  make clean       Remove build artifacts and caches"
	@echo "  make run         Quick smoke run on the example fixture"
	@echo "  make docs        Build and serve docs locally"
	@echo "  make build       Build distributable wheel"

install:
	uv sync

dev:
	uv sync --extra dev

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src/clearscript

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

run:
	uv run clearscript run examples/01-basic-cleanup/input.txt

docs:
	@if [ ! -d .venv-docs ]; then \
		uv venv .venv-docs --python 3.13; \
		uv pip install --python .venv-docs/bin/python "mkdocs-material>=9.5.0" "pymdown-extensions>=10.0"; \
	fi
	.venv-docs/bin/mkdocs serve

docs-build:
	@if [ ! -d .venv-docs ]; then \
		uv venv .venv-docs --python 3.13; \
		uv pip install --python .venv-docs/bin/python "mkdocs-material>=9.5.0" "pymdown-extensions>=10.0"; \
	fi
	.venv-docs/bin/mkdocs build --strict

build:
	uv build
