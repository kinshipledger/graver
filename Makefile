.PHONY: help init sync run test lint format clean

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

lint: ## Lint code using the configured Flake8 checks
	uv run --group test flake8 src/graver tests --count --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code using Black
	uv run --group dev black .

clean: ## Remove virtual environment and build artifacts
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -r {} +
