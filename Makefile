PROJECT_NAME = $(shell grep -m 1 name pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
VERSION = $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
PYTHON_VERSION = $(shell grep "^python = \"" pyproject.toml | sed 's/^python = "\(.*\)".*/\1/')

export SERVER_HOST ?= 0.0.0.0
export SERVER_PORT ?= 3000
export LOG_LEVEL ?= INFO
export AUTO_SAVE ?= true
ENVIRONMENT ?= development

.PHONY: setup start run debug test test-cov coverage format lint clean build install uninstall

version:
	@echo "$(PROJECT_NAME) v$(VERSION) (Python $(PYTHON_VERSION))"

setup:
	pyenv local $(PYTHON_VERSION)
	poetry env use $(PYTHON_VERSION)
	poetry lock
	poetry install

run: run-$(ENVIRONMENT)

run-production:
	poetry run gunicorn --bind $(SERVER_HOST):$(SERVER_PORT) \
		--workers 1 --log-level=$(LOG_LEVEL) \
		--access-logfile - --error-logfile - \
		"simple_api.flask:create_app()"

run-%:  # Catches all non-production environments
	poetry run python main.py

debug:
	poetry run python -m debugpy --listen 5678 --wait-for-client main.py

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=src/simple_api --cov-report=term-missing --cov-report=html

lint:
	poetry run black .
	poetry run isort .
	poetry run flake8
	poetry run mypy src
	poetry run bandit .

imports:
	poetry run deptry .

commit:
	git add . && poetry run cz commit && git push
