.PHONY: install dev frontend-install frontend-dev frontend-build test lint seed eval up down demo-escalate demo-jev-routing demo-harness test-real-ollama
install:
	uv sync --extra dev
dev:
	uv run uvicorn app.main:app --reload
frontend-install:
	npm --prefix frontend install
frontend-dev:
	npm --prefix frontend run dev
frontend-build:
	npm --prefix frontend run build
test:
	uv run pytest
lint:
	uv run ruff check app tests
seed:
	uv run python scripts/seed_demo_requests.py
eval:
	uv run python scripts/run_eval.py
demo-escalate:
	uv run python scripts/demo_escalate.py
demo-jev-routing:
	uv run python scripts/demo_jev_routing.py
demo-harness:
	uv run python scripts/demo_harness.py
test-real-ollama:
	uv run python scripts/test_real_ollama.py
up:
	docker compose up --build
down:
	docker compose down
