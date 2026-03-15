# Enterprise GenAI Document Q&A - Makefile

.PHONY: backend frontend docker test lint install-backend install-frontend

# Backend
install-backend:
	cd backend && python -m venv .venv 2>/dev/null || true
	cd backend && .venv/bin/pip install -r requirements.txt

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
install-frontend:
	cd frontend && npm install

frontend:
	cd frontend && npm run dev

# Docker
docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Tests
test:
	cd backend && .venv/bin/pytest -v

test-cov:
	cd backend && .venv/bin/pytest --cov=app -v

# Lint (optional)
lint-backend:
	cd backend && .venv/bin/ruff check app || true
	cd backend && .venv/bin/black --check app || true

lint-frontend:
	cd frontend && npm run lint || true
