.PHONY: install dev build test lint format

install:
	python -m pip install -e '.[dev]'

dev:
	blog dev --watch

build:
	blog build

test:
	pytest

lint:
	ruff check .

format:
	ruff format .
