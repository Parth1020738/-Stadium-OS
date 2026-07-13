# Aegis monorepo build orchestrator Makefile

.PHONY: setup run-infra reset-env format lint test

setup:
	@echo "Running environment setup..."
	@bash ./scripts/setup.sh

run-infra:
	@echo "Launching local databases, caches, and queues..."
	@bash ./scripts/run_local.sh

reset-env:
	@echo "Pruning infrastructure volumes..."
	@bash ./scripts/reset_environment.sh

format:
	@echo "Formatting TypeScript and Python files..."
	pnpm run format:ts
	@if command -v ruff > /dev/null; then ruff format .; fi

lint:
	@echo "Checking formatting and style constraints..."
	pnpm run lint:ts
	@if command -v ruff > /dev/null; then ruff check .; fi

test:
	@echo "Executing tests..."
	pnpm run test:ts
	@if command -v python > /dev/null; then python tests/backend/run_tests.py; fi
