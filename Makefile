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
	render-start:
	@echo "Checking Gunicorn installation..."
	uv pip show gunicorn || uv pip install gunicorn
	@echo "Starting server..."
	uv run gunicorn -w 4 -b 0.0.0.0:$(PORT) page_analyzer:app