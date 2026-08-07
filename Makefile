SHELL := /bin/bash

DEFAULT_MODE := git
MODE ?= $(DEFAULT_MODE)

.DEFAULT_GOAL := help

local:
	poetry run python -m debugpy --listen 0.0.0.0:5692 -m uvicorn talkingdb_nel.main:app --host 0.0.0.0 --port 8092 --reload --reload-dir ./ --reload-dir ../base-tdb-models --reload-dir ../base-tdb-clients --reload-dir ../base-tdb-helpers

format:
	poetry run ruff format .
	poetry run ruff check . --fix

lint:
	poetry run ruff check .

test:
	poetry run pytest

coverage:
	poetry run pytest --cov=talkingdb_nel --cov-report=term-missing --cov-report=html

check-format:
	poetry run ruff format . --check

check-lint:
	poetry run ruff check .

check: check-format check-lint test

sync:
	@echo "🔄 Running sync_git_deps.py with mode: $(MODE)"
	python3 sync_git_deps.py --mode "$(MODE)"

sync-dry-run:
	@echo "🔍 Dry-run sync for validation (mode: $(MODE))"
	python3 sync_git_deps.py --mode "$(MODE)" --dry-run

install-hooks:
	@echo "Installing git hooks..."
	@cp -f git-hooks/* .git/hooks/
	@chmod +x .git/hooks/*
	@echo "Git hooks installed!"

help:
	@echo ""
	@echo "Targets:"
	@echo "  make local"
	@echo "  make format"
	@echo "  make lint"
	@echo "  make test"
	@echo "  make coverage"
	@echo "  make check-format"
	@echo "  make check-lint"
	@echo "  make check"
	@echo "  make sync MODE=<git|local>"
	@echo "  make sync-dry-run MODE=<git|local>"
	@echo "  make install-hooks"
	@echo ""