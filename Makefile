PROJECT_NAME = $(shell grep -m 1 name pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
VERSION = $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
PYTHON_VERSION = $(shell grep "^python = \"" pyproject.toml | sed 's/^python = "\(.*\)".*/\1/')

export SERVER_HOST ?= 0.0.0.0
export SERVER_PORT ?= 3000
export LOG_LEVEL ?= INFO
export AUTO_SAVE ?= true
export ENVIRONMENT ?= development

.PHONY: setup start run debug test test-cov coverage format lint clean build install uninstall

version:
	@echo "$(PROJECT_NAME) v$(VERSION) (Python $(PYTHON_VERSION))"

setup:
	pyenv local $(PYTHON_VERSION)
	poetry env use $(PYTHON_VERSION)
	poetry lock
	poetry install

run:
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

import:
	poetry run deptry .

security:
	poetry run bandit -r src/ -c pyproject.toml -f screen
	poetry run safety scan
	poetry run pip-audit --desc --ignore-vuln GHSA-4xh5-x5gv-qwph

check: lint test

commit:
	git add . && poetry run cz commit && git push
