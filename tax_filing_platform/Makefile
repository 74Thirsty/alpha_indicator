.PHONY: install test lint format migrate run deploy-contract-local

install:
	python -m pip install -e backend[test,dev]

test:
	cd backend && pytest

lint:
	cd backend && ruff check app tests ../contracts/tests

format:
	cd backend && ruff format app tests ../contracts/tests

migrate:
	cd backend && alembic upgrade head

run:
	cd backend && uvicorn app.main:app --reload

deploy-contract-local:
	python contracts/deploy/deploy_local.py
