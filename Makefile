PROJECT_NAME = $(shell grep -m 1 name pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
VERSION = $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
PYTHON_VERSION = $(shell grep "^python = \"" pyproject.toml | sed 's/^python = "\(.*\)".*/\1/')

SERVER_HOST ?= 0.0.0.0
SERVER_PORT ?= 3000
LOG_LEVEL ?= INFO
AUTO_SAVE ?= true

.PHONY: setup start start-server debug test format lint clean build install uninstall

version:
	@echo "$(PROJECT_NAME) v$(VERSION) (Python $(PYTHON_VERSION))"

setup:
	pyenv local $(PYTHON_VERSION)
	poetry env use $(PYTHON_VERSION)
	poetry lock
	poetry install

start:
	export SERVER_HOST=$(SERVER_HOST) && \
	export SERVER_PORT=$(SERVER_PORT) && \
	export LOG_LEVEL=$(LOG_LEVEL) && \
	export AUTO_SAVE=$(AUTO_SAVE) && \
	poetry run python main.py

start-server:
	poetry run gunicorn --bind $(SERVER_HOST):$(SERVER_PORT) --workers 1 --log-level=$(LOG_LEVEL) --access-logfile - --error-logfile - "simple_api.app:create_app()"

debug:
	poetry run python -m debugpy --listen 5678 --wait-for-client main.py

test:
	poetry run pytest

lint:
	poetry run black .
	poetry run isort .
	poetry run flake8
	poetry run mypy src
	poetry run bandit .

imports:
	poetry run deptry .

check: lint test imports

commit:
	git add . && poetry run cz commit

bump:
	poetry run cz bump --changelog
