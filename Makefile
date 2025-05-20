install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run

build:
	./build.sh

lint:
	uvx ruff check --config ruff.toml --fix

test-coverage:
	uv run pytest --cov=gendiff --cov-report xml

PORT ?= 8000
start:
	uv run waitress-serve --host=0.0.0.0 --port=$(PORT) page_analyzer:app

render-start:
	waitress-serve --host=0.0.0.0 --port=$(PORT) page_analyzer:app