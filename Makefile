.PHONY: help init sync run test lint typecheck doccheck format clean

# Default goal when running just `make`
.DEFAULT_GOAL := help

PYTEST := python3 -m pytest

# Keep uv's cache in the project so Make targets work in sandboxed environments
# where the user's global cache directory is not writable.
export UV_CACHE_DIR := $(CURDIR)/.uv-cache

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Initialize a new project with uv
	uv init
	uv sync

sync: ## Synchronize dependencies from pyproject.toml / uv.lock
	uv sync

run: ## Run the main application
	uv run main.py

test: ## Run tests using pytest
	PYTHONPATH=src uv run --group test pytest

lint: ## Run required formatting and lint checks
	uv run --group dev black --check src/graver tests review consumer_spike
	uv run --group dev ruff check src/graver tests review consumer_spike

typecheck: ## Type-check the supported application boundary
	uv run --group dev mypy

doccheck: ## Check public application docstring coverage and style
	uv run --group dev ruff check --select D --ignore D105,D107 src/graver/application.py src/graver/database.py src/graver/evidence.py src/graver/research.py src/graver/workspace.py

format: ## Apply safe lint fixes and Black formatting
	uv run --group dev ruff check --fix src/graver tests review consumer_spike
	uv run --group dev black src/graver tests review consumer_spike

clean: ## Remove virtual environment and build artifacts
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -r {} +
