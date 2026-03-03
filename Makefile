.PHONY: dev lint format serve cli migrate

dev:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt && pip install -e .

lint:
	ruff check app cli
	mypy app cli

format:
	ruff format app cli

serve:
	alembic upgrade head
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

cli:
	ohmygreen

migrate:
	alembic upgrade head
