.PHONY: dev backend frontend lint format test cli doctor docker-up

dev:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt

backend:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 5173

lint:
	ruff check backend cli
	mypy backend cli

format:
	ruff format backend cli

test:
	pytest -q

cli:
	python -m cli.ohmygreen_cli.main

doctor:
	python -m cli.ohmygreen_cli.main doctor

docker-up:
	docker compose -f configs/docker-compose.yml up --build
