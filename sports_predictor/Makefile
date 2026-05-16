.PHONY: up down build logs migrate shell-api shell-db test

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up --build -d

logs:
	docker-compose logs -f api

logs-all:
	docker-compose logs -f

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

shell-api:
	docker-compose exec api bash

shell-db:
	docker-compose exec db psql -U user -d sportpredictor

generate:
	curl -s http://localhost:8000/api/v1/predictions/trigger | python3 -m json.tool

health:
	curl -s http://localhost:8000/api/v1/stats/health | python3 -m json.tool

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev
